"""API key management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, List, Optional
import uuid

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.requests import APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyList, ErrorResponse, ErrorDetail
from app.models.database import APIKey
from app.services.key_mapper import KeyMapperService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/keys", tags=["api_keys"])

@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Create a new API key.
    
    This endpoint creates a new API key associated with the authenticated organization
    and optionally with a specific user.
    
    Parameters:
    - **key_data**: API key creation data including OpenAI API key and optional user ID, name, and description
    
    Returns:
    - API key object with ID, organization ID, user ID, synthetic key, and other metadata
    
    Raises:
    - 400: Bad Request - If API key creation fails
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    
    Example:
    ```json
    {
      "openai_api_key": "sk-your-openai-key",
      "user_id": "user-uuid",
      "name": "Production API Key",
      "description": "API key for production environment"
    }
    ```
    """
    key_mapper = KeyMapperService(db)
    
    api_key = await key_mapper.create_api_key(
        organization_id=organization["organization_id"],
        openai_key=key_data.openai_api_key,
        user_id=key_data.user_id,
        name=key_data.name,
        description=key_data.description
    )
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create API key"
        )
    
    return APIKeyResponse(
        id=str(api_key.id),
        organization_id=str(api_key.organization_id),
        user_id=str(api_key.user_id) if api_key.user_id else None,
        synthetic_key=api_key.synthetic_key,
        is_active=api_key.is_active,
        name=api_key.name,
        description=api_key.description,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )

@router.get("", response_model=APIKeyList)
async def list_api_keys(
    user_id: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    List API keys, optionally filtered by user.
    
    This endpoint retrieves all API keys associated with the authenticated organization,
    with optional filtering by user ID and active status.
    
    Parameters:
    - **user_id**: Optional UUID of the user to filter by
    - **include_inactive**: Whether to include inactive API keys (default: false)
    
    Returns:
    - List of API key objects, each with ID, organization ID, user ID, synthetic key, and other metadata
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    key_mapper = KeyMapperService(db)
    
    api_keys = await key_mapper.get_api_keys(
        organization_id=organization["organization_id"],
        user_id=user_id,
        include_inactive=include_inactive
    )
    
    return APIKeyList(
        api_keys=[
            APIKeyResponse(
                id=str(key.id),
                organization_id=str(key.organization_id),
                user_id=str(key.user_id) if key.user_id else None,
                synthetic_key=key.synthetic_key,
                is_active=key.is_active,
                name=key.name,
                description=key.description,
                created_at=key.created_at,
                updated_at=key.updated_at
            )
            for key in api_keys
        ]
    )

@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get a specific API key by ID.
    
    This endpoint retrieves a specific API key by its UUID.
    
    Parameters:
    - **key_id**: UUID of the API key to retrieve
    
    Returns:
    - API key object with ID, organization ID, user ID, synthetic key, and other metadata
    
    Raises:
    - 400: Bad Request - If API key ID format is invalid
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission to access the API key
    - 404: Not Found - If API key doesn't exist
    """
    try:
        uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    # Get the API key
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key not found: {key_id}"
        )
    
    # Verify API key belongs to the organization
    if str(api_key.organization_id) != organization["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this API key"
        )
    
    return APIKeyResponse(
        id=str(api_key.id),
        organization_id=str(api_key.organization_id),
        user_id=str(api_key.user_id) if api_key.user_id else None,
        synthetic_key=api_key.synthetic_key,
        is_active=api_key.is_active,
        name=api_key.name,
        description=api_key.description,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )

@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    key_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Update an API key.
    
    This endpoint updates a specific API key by its UUID.
    
    Parameters:
    - **key_id**: UUID of the API key to update
    - **key_data**: API key update data including optional active status, user ID, name, description, and OpenAI API key
    
    Returns:
    - Updated API key object with ID, organization ID, user ID, synthetic key, and other metadata
    
    Raises:
    - 400: Bad Request - If API key ID format is invalid
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission to update the API key
    - 404: Not Found - If API key doesn't exist
    - 500: Internal Server Error - If update fails
    
    Example:
    ```json
    {
      "is_active": true,
      "user_id": "user-uuid",
      "name": "Updated Key Name",
      "description": "Updated description",
      "openai_api_key": "sk-new-openai-key"
    }
    ```
    """
    key_mapper = KeyMapperService(db)
    
    try:
        uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    # Get the API key first to verify organization
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key not found: {key_id}"
        )
    
    # Verify API key belongs to the organization
    if str(api_key.organization_id) != organization["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this API key"
        )
    
    # Update the API key
    updated_key = await key_mapper.update_api_key(
        key_id=key_id,
        is_active=key_data.is_active,
        user_id=key_data.user_id,
        name=key_data.name,
        description=key_data.description,
        openai_key=key_data.openai_api_key
    )
    
    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API key"
        )
    
    return APIKeyResponse(
        id=str(updated_key.id),
        organization_id=str(updated_key.organization_id),
        user_id=str(updated_key.user_id) if updated_key.user_id else None,
        synthetic_key=updated_key.synthetic_key,
        is_active=updated_key.is_active,
        name=updated_key.name,
        description=updated_key.description,
        created_at=updated_key.created_at,
        updated_at=updated_key.updated_at
    )

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Delete/deactivate an API key.
    
    This endpoint deactivates a specific API key by its UUID.
    Note: This is a soft delete that sets is_active to false.
    
    Parameters:
    - **key_id**: UUID of the API key to deactivate
    
    Returns:
    - 204 No Content on successful deactivation
    
    Raises:
    - 400: Bad Request - If API key ID format is invalid
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission to delete the API key
    - 404: Not Found - If API key doesn't exist
    - 500: Internal Server Error - If deactivation fails
    """
    key_mapper = KeyMapperService(db)
    
    try:
        uuid.UUID(key_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key ID format"
        )
    
    # Get the API key first to verify organization
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key not found: {key_id}"
        )
    
    # Verify API key belongs to the organization
    if str(api_key.organization_id) != organization["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this API key"
        )
    
    # Deactivate the API key (soft delete)
    updated_key = await key_mapper.update_api_key(
        key_id=key_id,
        is_active=False
    )
    
    if not updated_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate API key"
        )
