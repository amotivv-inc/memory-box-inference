"""Service for managing analysis configurations"""

from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.database import AnalysisConfig, User
from app.models.analysis import AnalysisConfigData
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class AnalysisConfigService:
    """Service for managing analysis configurations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def create_config(
        self,
        organization_id: str,
        name: str,
        description: Optional[str],
        config: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> AnalysisConfig:
        """Create a new analysis configuration"""
        # Validate config structure
        try:
            validated_config = AnalysisConfigData(**config)
        except Exception as e:
            raise ValueError(f"Invalid configuration: {str(e)}")
            
        # Check if name already exists for organization
        existing = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.organization_id == organization_id,
                    AnalysisConfig.name == name
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Configuration with name '{name}' already exists")
            
        # Get created_by user ID if provided
        created_by_id = None
        if created_by:
            user_result = await self.db.execute(
                select(User).where(
                    and_(
                        User.organization_id == organization_id,
                        User.user_id == created_by
                    )
                )
            )
            user = user_result.scalar_one_or_none()
            if user:
                created_by_id = user.id
                
        # Create configuration
        analysis_config = AnalysisConfig(
            id=uuid.uuid4(),
            organization_id=uuid.UUID(organization_id),
            name=name,
            description=description,
            config=validated_config.model_dump(),
            is_active=True,
            created_by=created_by_id
        )
        
        self.db.add(analysis_config)
        await self.db.commit()
        await self.db.refresh(analysis_config)
        
        logger.info(f"Created analysis config {analysis_config.id} for org {organization_id}")
        return analysis_config
        
    async def get_config(
        self,
        config_id: str,
        organization_id: str
    ) -> Optional[AnalysisConfig]:
        """Get a specific configuration"""
        result = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.id == config_id,
                    AnalysisConfig.organization_id == organization_id
                )
            )
        )
        return result.scalar_one_or_none()
        
    async def list_configs(
        self,
        organization_id: str,
        is_active: Optional[bool] = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List configurations for an organization"""
        # Build query
        query = select(AnalysisConfig).where(
            AnalysisConfig.organization_id == organization_id
        )
        
        if is_active is not None:
            query = query.where(AnalysisConfig.is_active == is_active)
            
        # Get total count
        count_query = select(func.count()).select_from(AnalysisConfig).where(
            AnalysisConfig.organization_id == organization_id
        )
        if is_active is not None:
            count_query = count_query.where(AnalysisConfig.is_active == is_active)
            
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        query = query.order_by(AnalysisConfig.created_at.desc())
        
        # Execute query
        result = await self.db.execute(query)
        configs = result.scalars().all()
        
        return {
            "items": configs,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    async def update_config(
        self,
        config_id: str,
        organization_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[AnalysisConfig]:
        """Update an analysis configuration"""
        # Get existing config
        result = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.id == config_id,
                    AnalysisConfig.organization_id == organization_id
                )
            )
        )
        analysis_config = result.scalar_one_or_none()
        
        if not analysis_config:
            return None
            
        # Check if new name conflicts
        if name and name != analysis_config.name:
            existing = await self.db.execute(
                select(AnalysisConfig).where(
                    and_(
                        AnalysisConfig.organization_id == organization_id,
                        AnalysisConfig.name == name,
                        AnalysisConfig.id != config_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ValueError(f"Configuration with name '{name}' already exists")
                
        # Update fields
        if name is not None:
            analysis_config.name = name
        if description is not None:
            analysis_config.description = description
        if config is not None:
            # Validate new config
            try:
                validated_config = AnalysisConfigData(**config)
                analysis_config.config = validated_config.model_dump()
            except Exception as e:
                raise ValueError(f"Invalid configuration: {str(e)}")
        if is_active is not None:
            analysis_config.is_active = is_active
            
        analysis_config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(analysis_config)
        
        logger.info(f"Updated analysis config {config_id}")
        return analysis_config
        
    async def delete_config(
        self,
        config_id: str,
        organization_id: str
    ) -> bool:
        """Delete (deactivate) an analysis configuration"""
        # Get existing config
        result = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.id == config_id,
                    AnalysisConfig.organization_id == organization_id
                )
            )
        )
        analysis_config = result.scalar_one_or_none()
        
        if not analysis_config:
            return False
            
        # Soft delete by deactivating
        analysis_config.is_active = False
        analysis_config.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Deactivated analysis config {config_id}")
        return True
        
    async def get_config_by_name(
        self,
        organization_id: str,
        name: str
    ) -> Optional[AnalysisConfig]:
        """Get a configuration by name"""
        result = await self.db.execute(
            select(AnalysisConfig).where(
                and_(
                    AnalysisConfig.organization_id == organization_id,
                    AnalysisConfig.name == name,
                    AnalysisConfig.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
