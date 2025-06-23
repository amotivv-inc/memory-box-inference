"""API endpoints for managing analysis configurations"""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging

from app.core import get_db, get_current_organization
from app.models.analysis import (
    AnalysisConfigCreate, AnalysisConfigUpdate, AnalysisConfig,
    AnalysisConfigList, AnalysisError
)
from app.services.analysis_config_service import AnalysisConfigService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis/configs", tags=["analysis-configs"])


@router.post(
    "",
    response_model=AnalysisConfig,
    summary="Create an analysis configuration",
    description="""
    Create a reusable analysis configuration for your organization.
    
    Configurations can define:
    - Analysis type (intent, sentiment, topic, etc.)
    - Categories to classify
    - Model settings
    - Custom prompts
    """,
    responses={
        201: {
            "description": "Configuration created successfully",
            "model": AnalysisConfig
        },
        400: {
            "description": "Invalid configuration data",
            "model": AnalysisError
        },
        401: {
            "description": "Unauthorized - Invalid JWT",
            "model": AnalysisError
        },
        409: {
            "description": "Conflict - Configuration name already exists",
            "model": AnalysisError
        }
    }
)
async def create_analysis_config(
    config_data: AnalysisConfigCreate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization),
    x_user_id: Optional[str] = Header(None, description="User ID for tracking")
):
    """Create a new analysis configuration"""
    try:
        config_service = AnalysisConfigService(db)
        
        config = await config_service.create_config(
            organization_id=organization["organization_id"],
            name=config_data.name,
            description=config_data.description,
            config=config_data.config.model_dump(),
            created_by=x_user_id
        )
        
        return AnalysisConfig.model_validate(config)
        
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        logger.error(f"Error creating analysis config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "",
    response_model=AnalysisConfigList,
    summary="List analysis configurations",
    description="""
    List all analysis configurations for your organization.
    
    Supports pagination and filtering by active status.
    """
)
async def list_analysis_configs(
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """List analysis configurations"""
    try:
        config_service = AnalysisConfigService(db)
        
        result = await config_service.list_configs(
            organization_id=organization["organization_id"],
            is_active=is_active,
            page=page,
            page_size=page_size
        )
        
        return AnalysisConfigList(
            items=[AnalysisConfig.model_validate(c) for c in result["items"]],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
        
    except Exception as e:
        logger.error(f"Error listing analysis configs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{config_id}",
    response_model=AnalysisConfig,
    summary="Get an analysis configuration",
    description="Get a specific analysis configuration by ID"
)
async def get_analysis_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Get a specific analysis configuration"""
    try:
        config_service = AnalysisConfigService(db)
        
        config = await config_service.get_config(
            config_id=config_id,
            organization_id=organization["organization_id"]
        )
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration {config_id} not found"
            )
            
        return AnalysisConfig.model_validate(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/{config_id}",
    response_model=AnalysisConfig,
    summary="Update an analysis configuration",
    description="Update an existing analysis configuration"
)
async def update_analysis_config(
    config_id: str,
    update_data: AnalysisConfigUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Update an analysis configuration"""
    try:
        config_service = AnalysisConfigService(db)
        
        config = await config_service.update_config(
            config_id=config_id,
            organization_id=organization["organization_id"],
            name=update_data.name,
            description=update_data.description,
            config=update_data.config.model_dump() if update_data.config else None,
            is_active=update_data.is_active
        )
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration {config_id} not found"
            )
            
        return AnalysisConfig.model_validate(config)
        
    except ValueError as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating analysis config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete(
    "/{config_id}",
    status_code=204,
    summary="Delete an analysis configuration",
    description="Delete (deactivate) an analysis configuration"
)
async def delete_analysis_config(
    config_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Delete an analysis configuration"""
    try:
        config_service = AnalysisConfigService(db)
        
        success = await config_service.delete_config(
            config_id=config_id,
            organization_id=organization["organization_id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration {config_id} not found"
            )
            
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis config: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/by-name/{name}",
    response_model=AnalysisConfig,
    summary="Get configuration by name",
    description="Get an analysis configuration by its name"
)
async def get_config_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Get configuration by name"""
    try:
        config_service = AnalysisConfigService(db)
        
        config = await config_service.get_config_by_name(
            organization_id=organization["organization_id"],
            name=name
        )
        
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Configuration with name '{name}' not found"
            )
            
        return AnalysisConfig.model_validate(config)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting config by name: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
