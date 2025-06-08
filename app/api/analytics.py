"""Analytics API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.analytics import ModelUsageResponse, RatedResponsesResponse
from app.services.analytics_service import AnalyticsService
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
