"""Service for managing users"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.database import User, Organization
import logging
import uuid

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(
        self,
        organization_id: str,
        user_id: str
    ) -> Optional[User]:
        """
        Create a new user in an organization
        
        Args:
            organization_id: UUID of the organization
            user_id: External user ID
            
        Returns:
            Created User model or None if error
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
            
            # Check if user already exists
            existing_result = await self.db.execute(
                select(User).where(
                    and_(
                        User.organization_id == organization_id,
                        User.user_id == user_id
                    )
                )
            )
            existing_user = existing_result.scalar_one_or_none()
            
            if existing_user:
                logger.warning(f"User already exists: {user_id} in organization {organization_id}")
                return existing_user
            
            # Create user
            user = User(
                organization_id=organization_id,
                user_id=user_id
            )
            
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await self.db.rollback()
            return None
    
    async def get_user(
        self,
        organization_id: str,
        user_id: str
    ) -> Optional[User]:
        """
        Get a user by organization and external user ID
        
        Args:
            organization_id: UUID of the organization
            user_id: External user ID
            
        Returns:
            User model or None if not found
        """
        try:
            result = await self.db.execute(
                select(User).where(
                    and_(
                        User.organization_id == organization_id,
                        User.user_id == user_id
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error retrieving user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by internal UUID
        
        Args:
            user_id: UUID of the user
            
        Returns:
            User model or None if not found
        """
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error retrieving user by ID: {e}")
            return None
    
    async def get_users(self, organization_id: str) -> List[User]:
        """
        Get all users in an organization
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            List of User models
        """
        try:
            result = await self.db.execute(
                select(User).where(User.organization_id == organization_id)
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving users: {e}")
            return []
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user
        
        Args:
            user_id: UUID of the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the user
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.error(f"User not found: {user_id}")
                return False
            
            # Delete the user
            await self.db.delete(user)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            await self.db.rollback()
            return False
