"""Service for managing personas"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.dialects.postgresql import JSONB
from typing import Dict, Any, List, Optional
import uuid
import logging

from app.models.database import Persona, User

logger = logging.getLogger(__name__)


class PersonaService:
    """Service for managing personas"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_persona(
        self,
        organization_id: str,
        name: str,
        content: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Persona:
        """
        Create a new persona
        
        Args:
            organization_id: Organization ID
            name: Name of the persona
            content: System prompt content
            description: Optional description
            user_id: Optional user ID to restrict the persona to
            metadata: Optional metadata for tagging, versioning, etc.
            
        Returns:
            Created persona
        """
        # If user_id is provided, get the internal user ID
        internal_user_id = None
        if user_id:
            user_result = await self.db.execute(
                select(User)
                .where(User.organization_id == organization_id)
                .where(User.user_id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                internal_user_id = user.id
            else:
                logger.warning(f"User {user_id} not found for organization {organization_id}")
        
        # Create the persona
        persona = Persona(
            id=uuid.uuid4(),
            organization_id=organization_id,
            user_id=internal_user_id,
            name=name,
            description=description,
            content=content,
            persona_metadata=metadata,
            is_active=True
        )
        
        self.db.add(persona)
        await self.db.commit()
        await self.db.refresh(persona)
        
        return persona
    
    async def get_persona(
        self,
        organization_id: str,
        persona_id: str
    ) -> Optional[Persona]:
        """
        Get a persona by ID
        
        Args:
            organization_id: Organization ID
            persona_id: Persona ID
            
        Returns:
            Persona if found, None otherwise
        """
        result = await self.db.execute(
            select(Persona)
            .where(Persona.organization_id == organization_id)
            .where(Persona.id == persona_id)
        )
        
        return result.scalar_one_or_none()
    
    async def get_persona_for_request(
        self,
        organization_id: str,
        persona_id: str,
        external_user_id: Optional[str] = None
    ) -> Optional[Persona]:
        """
        Get a persona for a request, checking user restrictions
        
        Args:
            organization_id: Organization ID
            persona_id: Persona ID
            external_user_id: External user ID
            
        Returns:
            Persona if found and accessible, None otherwise
        """
        query = (
            select(Persona)
            .where(Persona.organization_id == organization_id)
            .where(Persona.id == persona_id)
            .where(Persona.is_active == True)
        )
        
        # If external_user_id is provided, check if the persona is restricted to a user
        if external_user_id:
            # Get the internal user ID
            user_result = await self.db.execute(
                select(User)
                .where(User.organization_id == organization_id)
                .where(User.user_id == external_user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                # Persona is accessible if:
                # 1. It has no user restriction (user_id is NULL)
                # 2. It's restricted to this user
                query = query.where(
                    (Persona.user_id.is_(None)) | (Persona.user_id == user.id)
                )
            else:
                # User not found, only allow personas with no user restriction
                query = query.where(Persona.user_id.is_(None))
        else:
            # No user provided, only allow personas with no user restriction
            query = query.where(Persona.user_id.is_(None))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_persona(
        self,
        organization_id: str,
        persona_id: str,
        data: Dict[str, Any]
    ) -> Optional[Persona]:
        """
        Update a persona
        
        Args:
            organization_id: Organization ID
            persona_id: Persona ID
            data: Data to update
            
        Returns:
            Updated persona if found, None otherwise
        """
        # Get the persona
        persona = await self.get_persona(organization_id, persona_id)
        if not persona:
            return None
        
        # Handle user_id if provided
        if "user_id" in data:
            external_user_id = data.pop("user_id")
            if external_user_id:
                # Get the internal user ID
                user_result = await self.db.execute(
                    select(User)
                    .where(User.organization_id == organization_id)
                    .where(User.user_id == external_user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    persona.user_id = user.id
                else:
                    logger.warning(f"User {external_user_id} not found for organization {organization_id}")
            else:
                # Clear user restriction
                persona.user_id = None
        
        # Update other fields
        for key, value in data.items():
            if key == "metadata":
                # Handle metadata specially to map to persona_metadata
                persona.persona_metadata = value
            elif hasattr(persona, key) and value is not None:
                setattr(persona, key, value)
        
        await self.db.commit()
        await self.db.refresh(persona)
        
        return persona
    
    async def delete_persona(
        self,
        organization_id: str,
        persona_id: str
    ) -> bool:
        """
        Delete a persona
        
        Args:
            organization_id: Organization ID
            persona_id: Persona ID
            
        Returns:
            True if deleted, False otherwise
        """
        result = await self.db.execute(
            delete(Persona)
            .where(Persona.organization_id == organization_id)
            .where(Persona.id == persona_id)
        )
        
        await self.db.commit()
        
        return result.rowcount > 0
    
    async def list_personas(
        self,
        organization_id: str,
        external_user_id: Optional[str] = None,
        include_inactive: bool = False,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Persona]:
        """
        List personas for an organization with optional metadata filtering
        
        Args:
            organization_id: Organization ID
            external_user_id: Optional external user ID to filter by
            include_inactive: Whether to include inactive personas
            metadata_filters: Optional metadata filters for searching
            
        Returns:
            List of personas
        """
        query = (
            select(Persona)
            .where(Persona.organization_id == organization_id)
        )
        
        # Filter by active status if needed
        if not include_inactive:
            query = query.where(Persona.is_active == True)
        
        # Filter by user if provided
        if external_user_id:
            # Get the internal user ID
            user_result = await self.db.execute(
                select(User)
                .where(User.organization_id == organization_id)
                .where(User.user_id == external_user_id)
            )
            user = user_result.scalar_one_or_none()
            
            if user:
                # Include personas that:
                # 1. Have no user restriction (user_id is NULL)
                # 2. Are restricted to this user
                query = query.where(
                    (Persona.user_id.is_(None)) | (Persona.user_id == user.id)
                )
            else:
                # User not found, only include personas with no user restriction
                query = query.where(Persona.user_id.is_(None))
        
        # Apply metadata filters if provided
        if metadata_filters:
            query = self._apply_metadata_filters(query, metadata_filters)
        
        # Order by name
        query = query.order_by(Persona.name)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    def _apply_metadata_filters(self, query, metadata_filters: Dict[str, Any]):
        """
        Apply metadata filters to a query using PostgreSQL JSONB operators
        
        Args:
            query: SQLAlchemy query object
            metadata_filters: Dictionary of metadata filters
            
        Returns:
            Modified query with metadata filters applied
        """
        for key, value in metadata_filters.items():
            if key.startswith('metadata.'):
                # Remove 'metadata.' prefix to get the actual field path
                field_path = key[9:]  # Remove 'metadata.' prefix
                
                if field_path == 'tags':
                    # Special handling for tags - support both single tag and multiple tags
                    if isinstance(value, str):
                        # Single tag - check if array contains this tag
                        query = query.where(
                            Persona.persona_metadata['tags'].astext.contains(f'"{value}"')
                        )
                    elif isinstance(value, list):
                        # Multiple tags - check if array contains any of these tags
                        tag_conditions = []
                        for tag in value:
                            tag_conditions.append(
                                Persona.persona_metadata['tags'].astext.contains(f'"{tag}"')
                            )
                        query = query.where(or_(*tag_conditions))
                
                elif field_path == 'tags.all':
                    # Special handling for tags.all - array must contain ALL specified tags
                    if isinstance(value, list):
                        for tag in value:
                            query = query.where(
                                Persona.persona_metadata['tags'].astext.contains(f'"{tag}"')
                            )
                
                elif '.' in field_path:
                    # Nested field access (e.g., deployment.environment)
                    path_parts = field_path.split('.')
                    # Use JSONB path operator for nested access
                    json_path = '{' + ','.join(path_parts) + '}'
                    query = query.where(
                        Persona.persona_metadata.op('#>')(json_path).astext == str(value)
                    )
                
                else:
                    # Simple field match (e.g., status, version, department)
                    query = query.where(
                        Persona.persona_metadata[field_path].astext == str(value)
                    )
            
            elif key == 'metadata_exists':
                # Check if metadata field exists
                if isinstance(value, str):
                    query = query.where(
                        Persona.persona_metadata.op('?')(value)
                    )
                elif isinstance(value, list):
                    # Check if any of the fields exist
                    exists_conditions = []
                    for field in value:
                        exists_conditions.append(
                            Persona.persona_metadata.op('?')(field)
                        )
                    query = query.where(or_(*exists_conditions))
        
        return query
    
    async def get_external_user_id(self, internal_user_id: uuid.UUID) -> Optional[str]:
        """
        Get the external user ID for an internal user ID
        
        Args:
            internal_user_id: Internal user ID
            
        Returns:
            External user ID if found, None otherwise
        """
        if not internal_user_id:
            return None
            
        result = await self.db.execute(
            select(User.user_id)
            .where(User.id == internal_user_id)
        )
        
        return result.scalar_one_or_none()
