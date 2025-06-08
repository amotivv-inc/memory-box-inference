"""Analytics API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_organization
from app.models.analytics import ModelUsageResponse
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
