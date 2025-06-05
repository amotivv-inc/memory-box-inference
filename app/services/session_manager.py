"""Service for managing user sessions"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import User, Session, Organization
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class SessionManagerService:
    """Service for handling session management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_user(self, organization_id: str, user_id: str) -> User:
        """
        Get existing user or create new one
        
        Args:
            organization_id: UUID of the organization
            user_id: External user ID
            
        Returns:
            User model instance
        """
        # Try to get existing user
        result = await self.db.execute(
            select(User)
            .where(User.organization_id == organization_id)
            .where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                organization_id=organization_id,
                user_id=user_id
            )
            self.db.add(user)
            await self.db.flush()
            logger.info(f"Created new user {user_id} for organization {organization_id}")
        
        return user
    
    async def create_session(self, user: User) -> Session:
        """
        Create a new session for a user
        
        Args:
            user: User model instance
            
        Returns:
            Session model instance
        """
        session_id = f"sess_{uuid.uuid4().hex}"
        
        session = Session(
            user_id=user.id,
            session_id=session_id
        )
        self.db.add(session)
        await self.db.flush()
        
        logger.info(f"Created session {session_id} for user {user.user_id}")
        return session
    
    async def get_or_create_session(
        self, 
        organization_id: str, 
        user_id: str,
        session_id: Optional[str] = None
    ) -> Session:
        """
        Get existing session or create new one
        
        Args:
            organization_id: UUID of the organization
            user_id: External user ID
            session_id: Optional existing session ID
            
        Returns:
            Session model instance
        """
        # Get or create user first
        user = await self.get_or_create_user(organization_id, user_id)
        
        if session_id:
            # Try to get existing session
            result = await self.db.execute(
                select(Session)
                .where(Session.session_id == session_id)
                .where(Session.user_id == user.id)
                .where(Session.ended_at.is_(None))
            )
            session = result.scalar_one_or_none()
            
            if session:
                return session
        
        # Create new session
        return await self.create_session(user)
    
    async def end_session(self, session_id: str) -> bool:
        """
        End a session by setting ended_at timestamp
        
        Args:
            session_id: Session ID to end
            
        Returns:
            True if session was ended, False if not found
        """
        result = await self.db.execute(
            select(Session)
            .where(Session.session_id == session_id)
            .where(Session.ended_at.is_(None))
        )
        session = result.scalar_one_or_none()
        
        if session:
            session.ended_at = datetime.utcnow()
            await self.db.flush()
            logger.info(f"Ended session {session_id}")
            return True
        
        return False
    
    async def get_active_sessions_count(self, user_id: str) -> int:
        """
        Get count of active sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of active sessions
        """
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .where(Session.ended_at.is_(None))
        )
        sessions = result.scalars().all()
        return len(sessions)
