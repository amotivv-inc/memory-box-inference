"""User management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import uuid

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.requests import UserCreate, UserResponse, UserList, ErrorResponse, ErrorDetail
from app.services.user_service import UserService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Create a new user in the organization.
    
    This endpoint creates a new user associated with the authenticated organization.
    
    Parameters:
    - **user_data**: User creation data including external user ID
    
    Returns:
    - User object with ID, organization ID, user ID, and creation timestamp
    
    Raises:
    - 400: Bad Request - If user creation fails
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    
    Example:
    ```json
    {
      "user_id": "external-user-123"
    }
    ```
    """
    user_service = UserService(db)
    
    user = await user_service.create_user(
        organization_id=organization["organization_id"],
        user_id=user_data.user_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    return UserResponse(
        id=str(user.id),
        organization_id=str(user.organization_id),
        user_id=user.user_id,
        created_at=user.created_at
    )

@router.get("", response_model=UserList)
async def list_users(
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    List all users in the organization.
    
    This endpoint retrieves all users associated with the authenticated organization.
    
    Returns:
    - List of user objects, each with ID, organization ID, user ID, and creation timestamp
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    user_service = UserService(db)
    
    users = await user_service.get_users(organization["organization_id"])
    
    return UserList(
        users=[
            UserResponse(
                id=str(user.id),
                organization_id=str(user.organization_id),
                user_id=user.user_id,
                created_at=user.created_at
            )
            for user in users
        ]
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get a specific user by ID.
    
    This endpoint retrieves a specific user by their UUID.
    
    Parameters:
    - **user_id**: UUID of the user to retrieve
    
    Returns:
    - User object with ID, organization ID, user ID, and creation timestamp
    
    Raises:
    - 400: Bad Request - If user ID format is invalid
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission to access the user
    - 404: Not Found - If user doesn't exist
    """
    user_service = UserService(db)
    
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    # Verify user belongs to the organization
    if str(user.organization_id) != organization["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user"
        )
    
    return UserResponse(
        id=str(user.id),
        organization_id=str(user.organization_id),
        user_id=user.user_id,
        created_at=user.created_at
    )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Delete a user.
    
    This endpoint deletes a specific user by their UUID.
    
    Parameters:
    - **user_id**: UUID of the user to delete
    
    Returns:
    - 204 No Content on successful deletion
    
    Raises:
    - 400: Bad Request - If user ID format is invalid
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission to delete the user
    - 404: Not Found - If user doesn't exist
    - 500: Internal Server Error - If deletion fails
    """
    user_service = UserService(db)
    
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    
    # Get the user first to verify organization
    user = await user_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found: {user_id}"
        )
    
    # Verify user belongs to the organization
    if str(user.organization_id) != organization["organization_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user"
        )
    
    success = await user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )
