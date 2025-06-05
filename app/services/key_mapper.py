"""Service for mapping synthetic API keys to real OpenAI keys"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.database import APIKey, Organization, User
from app.core.security import decrypt_api_key, encrypt_api_key, generate_synthetic_key
import logging
import uuid

logger = logging.getLogger(__name__)


class KeyMapperService:
    """Service for handling API key mapping operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_openai_key(self, organization_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """
        Get the decrypted OpenAI API key for an organization or specific user
        
        Args:
            organization_id: UUID of the organization
            user_id: Optional UUID of the user
            
        Returns:
            Decrypted OpenAI API key or None if not found
        """
        try:
            # Build query
            query = select(APIKey).where(
                and_(
                    APIKey.organization_id == organization_id,
                    APIKey.is_active == True
                )
            )
            
            # Add user filter if provided
            if user_id:
                query = query.where(APIKey.user_id == user_id)
            
            # Execute query
            result = await self.db.execute(query.limit(1))
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                if user_id:
                    logger.warning(f"No active API key found for user {user_id} in organization {organization_id}")
                else:
                    logger.warning(f"No active API key found for organization {organization_id}")
                return None
            
            # Decrypt and return the key
            return decrypt_api_key(api_key.openai_api_key)
            
        except Exception as e:
            logger.error(f"Error retrieving API key: {e}")
            return None
    
    async def get_api_key_by_synthetic(self, synthetic_key: str) -> Optional[APIKey]:
        """
        Get API key record by synthetic key
        
        Args:
            synthetic_key: The synthetic API key
            
        Returns:
            APIKey model or None if not found
        """
        try:
            result = await self.db.execute(
                select(APIKey)
                .where(APIKey.synthetic_key == synthetic_key)
                .where(APIKey.is_active == True)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error retrieving API key by synthetic key: {e}")
            return None
    
    async def validate_api_key(self, synthetic_key: str) -> Optional[str]:
        """
        Validate a synthetic API key and return the decrypted OpenAI key
        
        Args:
            synthetic_key: The synthetic API key to validate
            
        Returns:
            Decrypted OpenAI API key or None if invalid
        """
        api_key = await self.get_api_key_by_synthetic(synthetic_key)
        if api_key:
            return decrypt_api_key(api_key.openai_api_key)
        return None
    
    async def create_api_key(
        self, 
        organization_id: str, 
        openai_key: str, 
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[APIKey]:
        """
        Create a new API key for an organization or user
        
        Args:
            organization_id: UUID of the organization
            openai_key: OpenAI API key to encrypt
            user_id: Optional UUID of the user
            name: Optional name for the key
            description: Optional description for the key
            
        Returns:
            Created APIKey model or None if error
        """
        try:
            # Verify organization exists
            org_result = await self.db.execute(
                select(Organization).where(Organization.id == organization_id)
            )
            organization = org_result.scalar_one_or_none()
            
            if not organization:
                logger.error(f"Organization not found: {organization_id}")
                return None
            
            # Verify user exists if provided
            if user_id:
                user_result = await self.db.execute(
                    select(User).where(
                        and_(
                            User.id == user_id,
                            User.organization_id == organization_id
                        )
                    )
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User not found: {user_id} in organization {organization_id}")
                    return None
            
            # Generate synthetic key
            synthetic_key = generate_synthetic_key()
            
            # Encrypt the OpenAI key
            encrypted_key = encrypt_api_key(openai_key)
            
            # Create API key record
            api_key = APIKey(
                organization_id=organization_id,
                user_id=user_id,
                synthetic_key=synthetic_key,
                openai_api_key=encrypted_key,
                name=name,
                description=description,
                is_active=True
            )
            
            self.db.add(api_key)
            await self.db.commit()
            await self.db.refresh(api_key)
            
            return api_key
            
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            await self.db.rollback()
            return None
    
    async def update_api_key(
        self,
        key_id: str,
        is_active: Optional[bool] = None,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        openai_key: Optional[str] = None
    ) -> Optional[APIKey]:
        """
        Update an API key
        
        Args:
            key_id: UUID of the API key to update
            is_active: Optional new active status
            user_id: Optional new user ID
            name: Optional new name
            description: Optional new description
            openai_key: Optional new OpenAI API key
            
        Returns:
            Updated APIKey model or None if error
        """
        try:
            # Get the API key
            result = await self.db.execute(
                select(APIKey).where(APIKey.id == key_id)
            )
            api_key = result.scalar_one_or_none()
            
            if not api_key:
                logger.error(f"API key not found: {key_id}")
                return None
            
            # Verify user exists if provided
            if user_id:
                user_result = await self.db.execute(
                    select(User).where(
                        and_(
                            User.id == user_id,
                            User.organization_id == api_key.organization_id
                        )
                    )
                )
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.error(f"User not found: {user_id} in organization {api_key.organization_id}")
                    return None
            
            # Update fields
            if is_active is not None:
                api_key.is_active = is_active
            
            if user_id is not None:
                api_key.user_id = user_id
            
            if name is not None:
                api_key.name = name
            
            if description is not None:
                api_key.description = description
            
            if openai_key:
                api_key.openai_api_key = encrypt_api_key(openai_key)
            
            await self.db.commit()
            await self.db.refresh(api_key)
            
            return api_key
            
        except Exception as e:
            logger.error(f"Error updating API key: {e}")
            await self.db.rollback()
            return None
    
    async def get_api_keys(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[APIKey]:
        """
        Get API keys for an organization or user
        
        Args:
            organization_id: UUID of the organization
            user_id: Optional UUID of the user
            include_inactive: Whether to include inactive keys
            
        Returns:
            List of APIKey models
        """
        try:
            # Build query
            query = select(APIKey).where(APIKey.organization_id == organization_id)
            
            # Add user filter if provided
            if user_id:
                query = query.where(APIKey.user_id == user_id)
            
            # Add active filter if not including inactive
            if not include_inactive:
                query = query.where(APIKey.is_active == True)
            
            # Execute query
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving API keys: {e}")
            return []
    
    async def get_api_key_for_request(
        self, 
        organization_id: str, 
        user_id: str
    ) -> Optional[APIKey]:
        """
        Get the appropriate API key for a request, considering user scoping
        
        Priority:
        1. User-specific API key (if exists and active)
        2. Organization-wide API key (if exists and active)
        
        Args:
            organization_id: UUID of the organization
            user_id: UUID of the user making the request
            
        Returns:
            APIKey model or None if no suitable key found
        """
        try:
            # First, try to find a user-specific key
            user_key_result = await self.db.execute(
                select(APIKey).where(
                    and_(
                        APIKey.organization_id == organization_id,
                        APIKey.user_id == user_id,
                        APIKey.is_active == True
                    )
                ).limit(1)
            )
            user_key = user_key_result.scalar_one_or_none()
            
            if user_key:
                logger.info(f"Found user-specific API key for user {user_id}")
                return user_key
            
            # If no user-specific key, try organization-wide key
            org_key_result = await self.db.execute(
                select(APIKey).where(
                    and_(
                        APIKey.organization_id == organization_id,
                        APIKey.user_id.is_(None),  # Explicitly NULL
                        APIKey.is_active == True
                    )
                ).limit(1)
            )
            org_key = org_key_result.scalar_one_or_none()
            
            if org_key:
                logger.info(f"Found organization-wide API key for user {user_id}")
                return org_key
            
            logger.warning(f"No suitable API key found for user {user_id} in organization {organization_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving API key for request: {e}")
            return None
