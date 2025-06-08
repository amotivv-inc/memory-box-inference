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


class RatedResponseItem(BaseModel):
    """Details of a single rated response"""
    request_id: str = Field(..., description="Unique request ID", examples=["req_1234567890abcdef"])
    response_id: Optional[str] = Field(None, description="OpenAI response ID", examples=["resp_1234567890abcdef"])
    user_id: str = Field(..., description="External user ID", examples=["user123"])
    model: str = Field(..., description="Model used for the response", examples=["gpt-4o"])
    rating: int = Field(..., description="Rating value: -1 (negative), 0 (neutral), 1 (positive)", examples=[1])
    rating_feedback: Optional[str] = Field(None, description="Optional feedback text", examples=["Very helpful response"])
    rating_timestamp: datetime = Field(..., description="When the rating was submitted", examples=["2025-06-01T12:34:56Z"])
    created_at: datetime = Field(..., description="When the request was created", examples=["2025-06-01T12:30:00Z"])
    completed_at: Optional[datetime] = Field(None, description="When the request was completed", examples=["2025-06-01T12:30:05Z"])
    input_preview: str = Field(..., description="Preview of the input text", examples=["Tell me about artificial intelligence..."])
    output_preview: str = Field(..., description="Preview of the output text", examples=["Artificial intelligence (AI) is a branch of computer science..."])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "req_1234567890abcdef",
                "response_id": "resp_1234567890abcdef",
                "user_id": "user123",
                "model": "gpt-4o",
                "rating": 1,
                "rating_feedback": "Very helpful response",
                "rating_timestamp": "2025-06-01T12:34:56Z",
                "created_at": "2025-06-01T12:30:00Z",
                "completed_at": "2025-06-01T12:30:05Z",
                "input_preview": "Tell me about artificial intelligence...",
                "output_preview": "Artificial intelligence (AI) is a branch of computer science..."
            }
        }
    }


class RatedResponsesResponse(BaseModel):
    """Response model for rated responses analytics"""
    rated_responses: List[RatedResponseItem] = Field(..., description="List of rated responses")
    total_count: int = Field(..., description="Total number of rated responses", examples=[100])
    positive_count: int = Field(..., description="Number of positive ratings (1)", examples=[75])
    negative_count: int = Field(..., description="Number of negative ratings (-1)", examples=[15])
    neutral_count: int = Field(..., description="Number of neutral ratings (0)", examples=[10])
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    filtered_by_user: Optional[str] = Field(None, description="User ID filter applied", examples=["user123"])
    filtered_by_session: Optional[str] = Field(None, description="Session ID filter applied", examples=["sess_1234567890"])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rated_responses": [
                    {
                        "request_id": "req_1234567890abcdef",
                        "response_id": "resp_1234567890abcdef",
                        "user_id": "user123",
                        "model": "gpt-4o",
                        "rating": 1,
                        "rating_feedback": "Very helpful response",
                        "rating_timestamp": "2025-06-01T12:34:56Z",
                        "created_at": "2025-06-01T12:30:00Z",
                        "completed_at": "2025-06-01T12:30:05Z",
                        "input_preview": "Tell me about artificial intelligence...",
                        "output_preview": "Artificial intelligence (AI) is a branch of computer science..."
                    }
                ],
                "total_count": 100,
                "positive_count": 75,
                "negative_count": 15,
                "neutral_count": 10,
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z",
                "filtered_by_user": "user123",
                "filtered_by_session": "sess_1234567890"
            }
        }
    }
