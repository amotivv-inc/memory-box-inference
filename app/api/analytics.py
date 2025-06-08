"""Analytics API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.analytics import (
    ModelUsageResponse, RatedResponsesResponse, UserUsageResponse, 
    SessionsResponse, PersonaUsageResponse, PersonaDetailResponse
)
from app.services.analytics_service import AnalyticsService
from app.services.persona_service import PersonaService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/models", response_model=ModelUsageResponse)
async def get_model_usage(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get usage statistics by model.
    
    This endpoint provides analytics on model usage, including request counts,
    token usage, costs, and success rates.
    
    Parameters:
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    
    Returns:
    - Model usage statistics including counts, tokens, costs, and success rates
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"Analytics request for organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        result = await analytics_service.get_model_usage(
            organization_id=organization["organization_id"],
            start_date=start_date,
            end_date=end_date
        )
        
        return ModelUsageResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in get_model_usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analytics data: {str(e)}"
        )


@router.get("/rated-responses", response_model=RatedResponsesResponse)
async def get_rated_responses(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    rating: Optional[int] = Query(None, ge=-1, le=1, description="Filter by rating value (-1, 0, 1)"),
    user_id: Optional[str] = Query(None, description="Filter by external user ID"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get rated responses for an organization.
    
    This endpoint provides analytics on rated responses by users within the organization,
    including the rating value, feedback, and previews of the input and output.
    
    Parameters:
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    - **rating**: Optional filter by rating value (-1 for negative, 0 for neutral, 1 for positive)
    - **user_id**: Optional filter by external user ID
    - **session_id**: Optional filter by session ID
    - **limit**: Maximum number of results to return (default: 50, max: 100)
    - **offset**: Pagination offset (default: 0)
    
    Returns:
    - List of rated responses with rating details and statistics
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"Rated responses request for organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        result = await analytics_service.get_rated_responses(
            organization_id=organization["organization_id"],
            start_date=start_date,
            end_date=end_date,
            rating=rating,
            user_id=user_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return RatedResponsesResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in get_rated_responses: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving rated responses data: {str(e)}"
        )


@router.get("/user-usage", response_model=UserUsageResponse)
async def get_user_usage(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[str] = Query(None, description="Filter by external user ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get usage statistics by user.
    
    This endpoint provides analytics on API usage grouped by user within the organization,
    including request counts, token usage, costs, and success rates.
    
    Parameters:
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    - **user_id**: Optional filter for a specific user
    - **limit**: Maximum number of results to return (default: 50, max: 100)
    - **offset**: Pagination offset (default: 0)
    
    Returns:
    - Usage statistics by user including counts, tokens, costs, and success rates
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"User usage request for organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        result = await analytics_service.get_user_usage(
            organization_id=organization["organization_id"],
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return UserUsageResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in get_user_usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user usage data: {str(e)}"
        )


@router.get("/personas", response_model=PersonaUsageResponse)
async def get_persona_usage(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[str] = Query(None, description="Filter by external user ID"),
    include_inactive: bool = Query(False, description="Include inactive personas"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get usage statistics by persona.
    
    This endpoint provides analytics on persona usage, including request counts,
    token usage, costs, and success rates.
    
    Parameters:
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    - **user_id**: Optional filter by external user ID
    - **include_inactive**: Whether to include inactive personas (default: false)
    - **limit**: Maximum number of results to return (default: 50, max: 100)
    - **offset**: Pagination offset (default: 0)
    
    Returns:
    - Persona usage statistics including counts, tokens, costs, and success rates
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"Persona usage request for organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        result = await analytics_service.get_persona_usage(
            organization_id=organization["organization_id"],
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            include_inactive=include_inactive,
            limit=limit,
            offset=offset
        )
        
        return PersonaUsageResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in get_persona_usage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving persona usage data: {str(e)}"
        )


@router.get("/sessions", response_model=SessionsResponse)
async def get_sessions(
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[str] = Query(None, description="Filter by external user ID"),
    include_active: bool = Query(True, description="Include active sessions"),
    include_completed: bool = Query(True, description="Include completed sessions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get session analytics for an organization.
    
    This endpoint provides analytics on user sessions, including duration, request counts,
    token usage, and costs. It can show both active and completed sessions over time.
    
    Parameters:
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    - **user_id**: Optional filter by external user ID
    - **include_active**: Whether to include active sessions (default: true)
    - **include_completed**: Whether to include completed sessions (default: true)
    - **limit**: Maximum number of results to return (default: 50, max: 100)
    - **offset**: Pagination offset (default: 0)
    
    Returns:
    - List of sessions with analytics data and summary statistics
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    """
    try:
        logger.info(f"Sessions request for organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        result = await analytics_service.get_sessions(
            organization_id=organization["organization_id"],
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            include_active=include_active,
            include_completed=include_completed,
            limit=limit,
            offset=offset
        )
        
        return SessionsResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in get_sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving sessions data: {str(e)}"
        )


@router.get("/personas/{persona_id}", response_model=PersonaDetailResponse)
async def get_persona_details(
    persona_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    user_id: Optional[str] = Query(None, description="Filter by external user ID"),
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """
    Get detailed analytics for a specific persona.
    
    This endpoint provides comprehensive analytics for a specific persona,
    including usage statistics, temporal trends, and user information.
    
    Parameters:
    - **persona_id**: ID of the persona to analyze
    - **start_date**: Optional start date for filtering (defaults to 30 days ago)
    - **end_date**: Optional end date for filtering (defaults to current time)
    - **user_id**: Optional filter by external user ID
    
    Returns:
    - Detailed persona analytics including usage statistics, trends, and user data
    
    Raises:
    - 401: Unauthorized - If JWT authentication fails
    - 403: Forbidden - If organization doesn't have permission
    - 404: Not Found - If the persona doesn't exist or isn't accessible
    """
    try:
        logger.info(f"Persona details request for persona {persona_id} in organization {organization['organization_id']}")
        analytics_service = AnalyticsService(db)
        
        # Validate persona ID format
        try:
            import uuid
            persona_uuid = uuid.UUID(persona_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid persona ID format"
            )
        
        # Check if persona exists and belongs to the organization
        persona_service = PersonaService(db)
        persona = await persona_service.get_persona(
            organization_id=organization["organization_id"],
            persona_id=persona_id
        )
        
        if not persona:
            raise HTTPException(
                status_code=404,
                detail=f"Persona with ID {persona_id} not found"
            )
        
        result = await analytics_service.get_persona_details(
            organization_id=organization["organization_id"],
            persona_id=persona_id,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        return PersonaDetailResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_persona_details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving persona details: {str(e)}"
        )
