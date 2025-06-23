"""API endpoints for conversation analysis"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging

from app.core import get_db, get_current_organization
from app.core.dependencies import validate_user_id
from app.models.analysis import (
    AnalysisRequest, AnalysisResponse, AnalysisError
)
from app.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post(
    "",
    response_model=AnalysisResponse,
    summary="Analyze a conversation",
    description="""
    Analyze a request/response conversation for intents, sentiments, topics, or any custom classification.
    
    You can provide either:
    1. A saved configuration ID (config_id)
    2. An inline configuration (config)
    3. Both (inline config overrides saved config)
    
    By default, each analysis will be performed fresh. Set use_cache=true to use cached results when available.
    """,
    responses={
        200: {
            "description": "Successful analysis",
            "model": AnalysisResponse
        },
        400: {
            "description": "Invalid request or configuration",
            "model": AnalysisError
        },
        401: {
            "description": "Unauthorized - Invalid JWT",
            "model": AnalysisError
        },
        403: {
            "description": "Forbidden - Not authorized to analyze this request",
            "model": AnalysisError
        },
        404: {
            "description": "Request/Response not found",
            "model": AnalysisError
        },
        500: {
            "description": "Internal server error",
            "model": AnalysisError
        }
    }
)
async def analyze_conversation(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization),
    x_user_id: str = Depends(validate_user_id)
):
    """Analyze a conversation for intents, sentiments, or other categories"""
    try:
        # Validate request
        if not request.config_id and not request.config:
            raise HTTPException(
                status_code=400,
                detail="Either config_id or config must be provided"
            )
            
        # Create service
        analysis_service = AnalysisService(db)
        
        # Perform analysis
        result = await analysis_service.analyze(
            id=request.id,
            config_id=str(request.config_id) if request.config_id else None,
            config=request.config.model_dump() if request.config else None,
            config_overrides=request.config_overrides,
            organization_id=organization["organization_id"],
            user_id=x_user_id,
            use_cache=request.use_cache
        )
        
        return AnalysisResponse(**result)
        
    except ValueError as e:
        # Handle specific errors
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg)
        elif "not authorized" in error_msg.lower():
            raise HTTPException(status_code=403, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
            
    except Exception as e:
        logger.error(f"Error in analyze_conversation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="Get a previous analysis result",
    description="""
    Retrieve a previously performed analysis by its ID.
    
    This endpoint allows you to fetch historical analysis results.
    """,
    responses={
        200: {
            "description": "Analysis result found",
            "model": AnalysisResponse
        },
        401: {
            "description": "Unauthorized - Invalid JWT",
            "model": AnalysisError
        },
        403: {
            "description": "Forbidden - Not authorized to view this analysis",
            "model": AnalysisError
        },
        404: {
            "description": "Analysis not found",
            "model": AnalysisError
        }
    }
)
async def get_analysis_result(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Get a previous analysis result"""
    # This endpoint is for future use when we want to retrieve
    # analysis results by their ID
    raise HTTPException(
        status_code=501,
        detail="This endpoint is not yet implemented"
    )
