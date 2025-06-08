"""Pydantic models for analytics API responses"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ModelUsageItem(BaseModel):
    """Usage statistics for a single model"""
    model: str = Field(..., description="Model name", examples=["gpt-4o"])
    request_count: int = Field(..., description="Number of requests", examples=[150])
    success_count: int = Field(..., description="Number of successful requests", examples=[145])
    failure_count: int = Field(..., description="Number of failed requests", examples=[5])
    success_rate: float = Field(..., description="Success rate percentage", examples=[96.7])
    input_tokens: Optional[int] = Field(None, description="Total input tokens", examples=[15000])
    output_tokens: Optional[int] = Field(None, description="Total output tokens", examples=[45000])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[60000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[1.25])
    avg_response_time: Optional[float] = Field(None, description="Average response time in seconds", examples=[1.5])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model": "gpt-4o",
                "request_count": 150,
                "success_count": 145,
                "failure_count": 5,
                "success_rate": 96.7,
                "input_tokens": 15000,
                "output_tokens": 45000,
                "total_tokens": 60000,
                "total_cost": 1.25,
                "avg_response_time": 1.5
            }
        }
    }


class ModelUsageResponse(BaseModel):
    """Response model for model usage analytics"""
    models: List[ModelUsageItem] = Field(..., description="Usage statistics by model")
    total_requests: int = Field(..., description="Total number of requests", examples=[200])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[2.50])
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "models": [
                    {
                        "model": "gpt-4o",
                        "request_count": 150,
                        "success_count": 145,
                        "failure_count": 5,
                        "success_rate": 96.7,
                        "input_tokens": 15000,
                        "output_tokens": 45000,
                        "total_tokens": 60000,
                        "total_cost": 1.25,
                        "avg_response_time": 1.5
                    }
                ],
                "total_requests": 200,
                "total_cost": 2.50,
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z"
            }
        }
    }
