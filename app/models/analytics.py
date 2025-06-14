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


class UserUsageItem(BaseModel):
    """Usage statistics for a single user"""
    user_id: str = Field(..., description="External user ID", examples=["user123"])
    request_count: int = Field(..., description="Number of requests", examples=[150])
    success_count: int = Field(..., description="Number of successful requests", examples=[145])
    failure_count: int = Field(..., description="Number of failed requests", examples=[5])
    success_rate: float = Field(..., description="Success rate percentage", examples=[96.7])
    input_tokens: Optional[int] = Field(None, description="Total input tokens", examples=[15000])
    output_tokens: Optional[int] = Field(None, description="Total output tokens", examples=[45000])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[60000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[1.25])
    avg_response_time: Optional[float] = Field(None, description="Average response time in seconds", examples=[1.5])
    last_request_at: Optional[datetime] = Field(None, description="Timestamp of last request", examples=["2025-06-01T12:34:56Z"])
    models_used: List[str] = Field(default_factory=list, description="List of models used", examples=[["gpt-4o", "gpt-4o-mini"]])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user123",
                "request_count": 150,
                "success_count": 145,
                "failure_count": 5,
                "success_rate": 96.7,
                "input_tokens": 15000,
                "output_tokens": 45000,
                "total_tokens": 60000,
                "total_cost": 1.25,
                "avg_response_time": 1.5,
                "last_request_at": "2025-06-01T12:34:56Z",
                "models_used": ["gpt-4o", "gpt-4o-mini"]
            }
        }
    }


class UserUsageResponse(BaseModel):
    """Response model for user usage analytics"""
    users: List[UserUsageItem] = Field(..., description="Usage statistics by user")
    total_users: int = Field(..., description="Total number of users", examples=[10])
    total_requests: int = Field(..., description="Total number of requests", examples=[200])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[2.50])
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    filtered_by_user: Optional[str] = Field(None, description="User ID filter applied", examples=["user123"])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [
                    {
                        "user_id": "user123",
                        "request_count": 150,
                        "success_count": 145,
                        "failure_count": 5,
                        "success_rate": 96.7,
                        "input_tokens": 15000,
                        "output_tokens": 45000,
                        "total_tokens": 60000,
                        "total_cost": 1.25,
                        "avg_response_time": 1.5,
                        "last_request_at": "2025-06-01T12:34:56Z",
                        "models_used": ["gpt-4o", "gpt-4o-mini"]
                    }
                ],
                "total_users": 10,
                "total_requests": 200,
                "total_cost": 2.50,
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z",
                "filtered_by_user": "user123"
            }
        }
    }


class SessionItem(BaseModel):
    """Analytics for a single session"""
    session_id: str = Field(..., description="Unique session identifier", examples=["sess_1234567890abcdef"])
    user_id: str = Field(..., description="External user ID", examples=["user123"])
    started_at: datetime = Field(..., description="When the session started", examples=["2025-06-01T12:00:00Z"])
    ended_at: Optional[datetime] = Field(None, description="When the session ended (null if still active)", examples=["2025-06-01T12:30:00Z"])
    duration_minutes: Optional[float] = Field(None, description="Session duration in minutes", examples=[30.5])
    request_count: int = Field(..., description="Number of requests in this session", examples=[15])
    total_tokens: Optional[int] = Field(None, description="Total tokens used in this session", examples=[5000])
    total_cost: Optional[float] = Field(None, description="Total cost of this session in USD", examples=[0.25])
    models_used: List[str] = Field(default_factory=list, description="Models used in this session", examples=[["gpt-4o", "gpt-4o-mini"]])
    is_active: bool = Field(..., description="Whether the session is still active", examples=[False])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_1234567890abcdef",
                "user_id": "user123",
                "started_at": "2025-06-01T12:00:00Z",
                "ended_at": "2025-06-01T12:30:00Z",
                "duration_minutes": 30.5,
                "request_count": 15,
                "total_tokens": 5000,
                "total_cost": 0.25,
                "models_used": ["gpt-4o", "gpt-4o-mini"],
                "is_active": False
            }
        }
    }


class SessionsResponse(BaseModel):
    """Response model for sessions analytics"""
    sessions: List[SessionItem] = Field(..., description="List of session analytics")
    total_sessions: int = Field(..., description="Total number of sessions", examples=[100])
    active_sessions: int = Field(..., description="Number of currently active sessions", examples=[25])
    total_requests: int = Field(..., description="Total number of requests across all sessions", examples=[1500])
    total_cost: Optional[float] = Field(None, description="Total cost across all sessions in USD", examples=[25.50])
    avg_session_duration: Optional[float] = Field(None, description="Average session duration in minutes", examples=[15.3])
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    filtered_by_user: Optional[str] = Field(None, description="User ID filter applied", examples=["user123"])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sessions": [
                    {
                        "session_id": "sess_1234567890abcdef",
                        "user_id": "user123",
                        "started_at": "2025-06-01T12:00:00Z",
                        "ended_at": "2025-06-01T12:30:00Z",
                        "duration_minutes": 30.5,
                        "request_count": 15,
                        "total_tokens": 5000,
                        "total_cost": 0.25,
                        "models_used": ["gpt-4o", "gpt-4o-mini"],
                        "is_active": False
                    }
                ],
                "total_sessions": 100,
                "active_sessions": 25,
                "total_requests": 1500,
                "total_cost": 25.50,
                "avg_session_duration": 15.3,
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z",
                "filtered_by_user": "user123"
            }
        }
    }


class PersonaUsageItem(BaseModel):
    """Usage statistics for a single persona"""
    persona_id: str = Field(..., description="Persona ID", examples=["123e4567-e89b-12d3-a456-426614174000"])
    name: str = Field(..., description="Persona name", examples=["Customer Support Agent"])
    description: Optional[str] = Field(None, description="Persona description", examples=["A helpful customer support agent"])
    user_id: Optional[str] = Field(None, description="User ID if persona is restricted", examples=["user123"])
    request_count: int = Field(..., description="Number of requests using this persona", examples=[150])
    success_count: int = Field(..., description="Number of successful requests", examples=[145])
    failure_count: int = Field(..., description="Number of failed requests", examples=[5])
    success_rate: float = Field(..., description="Success rate percentage", examples=[96.7])
    input_tokens: Optional[int] = Field(None, description="Total input tokens", examples=[15000])
    output_tokens: Optional[int] = Field(None, description="Total output tokens", examples=[45000])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[60000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[1.25])
    avg_response_time: Optional[float] = Field(None, description="Average response time in seconds", examples=[1.5])
    last_used_at: Optional[datetime] = Field(None, description="Timestamp of last use", examples=["2025-06-01T12:34:56Z"])
    models_used: List[str] = Field(default_factory=list, description="List of models used with this persona", examples=[["gpt-4o", "gpt-4o-mini"]])
    is_active: bool = Field(..., description="Whether the persona is active", examples=[True])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Customer Support Agent",
                "description": "A helpful customer support agent",
                "user_id": "user123",
                "request_count": 150,
                "success_count": 145,
                "failure_count": 5,
                "success_rate": 96.7,
                "input_tokens": 15000,
                "output_tokens": 45000,
                "total_tokens": 60000,
                "total_cost": 1.25,
                "avg_response_time": 1.5,
                "last_used_at": "2025-06-01T12:34:56Z",
                "models_used": ["gpt-4o", "gpt-4o-mini"],
                "is_active": True
            }
        }
    }


class PersonaUsageResponse(BaseModel):
    """Response model for persona usage analytics"""
    personas: List[PersonaUsageItem] = Field(..., description="Usage statistics by persona")
    total_personas: int = Field(..., description="Total number of personas", examples=[10])
    total_requests: int = Field(..., description="Total number of requests using personas", examples=[200])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[2.50])
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    filtered_by_user: Optional[str] = Field(None, description="User ID filter applied", examples=["user123"])
    include_inactive: bool = Field(..., description="Whether inactive personas are included", examples=[False])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "personas": [
                    {
                        "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Customer Support Agent",
                        "description": "A helpful customer support agent",
                        "user_id": "user123",
                        "request_count": 150,
                        "success_count": 145,
                        "failure_count": 5,
                        "success_rate": 96.7,
                        "input_tokens": 15000,
                        "output_tokens": 45000,
                        "total_tokens": 60000,
                        "total_cost": 1.25,
                        "avg_response_time": 1.5,
                        "last_used_at": "2025-06-01T12:34:56Z",
                        "models_used": ["gpt-4o", "gpt-4o-mini"],
                        "is_active": True
                    }
                ],
                "total_personas": 10,
                "total_requests": 200,
                "total_cost": 2.50,
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z",
                "filtered_by_user": "user123",
                "include_inactive": False
            }
        }
    }


class DailyUsageItem(BaseModel):
    """Daily usage statistics for a persona"""
    date: str = Field(..., description="Date in YYYY-MM-DD format", examples=["2025-06-01"])
    request_count: int = Field(..., description="Number of requests on this date", examples=[25])
    success_count: int = Field(..., description="Number of successful requests", examples=[24])
    failure_count: int = Field(..., description="Number of failed requests", examples=[1])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[10000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[0.25])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2025-06-01",
                "request_count": 25,
                "success_count": 24,
                "failure_count": 1,
                "total_tokens": 10000,
                "total_cost": 0.25
            }
        }
    }


class UserUsageSummary(BaseModel):
    """Summary of usage by a user for a specific persona"""
    user_id: str = Field(..., description="External user ID", examples=["user123"])
    request_count: int = Field(..., description="Number of requests", examples=[75])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[30000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[0.75])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user123",
                "request_count": 75,
                "total_tokens": 30000,
                "total_cost": 0.75
            }
        }
    }


class ModelUsageSummary(BaseModel):
    """Summary of usage by model for a specific persona"""
    model: str = Field(..., description="Model name", examples=["gpt-4o"])
    request_count: int = Field(..., description="Number of requests", examples=[100])
    input_tokens: Optional[int] = Field(None, description="Total input tokens", examples=[10000])
    output_tokens: Optional[int] = Field(None, description="Total output tokens", examples=[30000])
    total_tokens: Optional[int] = Field(None, description="Total tokens used", examples=[40000])
    total_cost: Optional[float] = Field(None, description="Total cost in USD", examples=[1.00])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model": "gpt-4o",
                "request_count": 100,
                "input_tokens": 10000,
                "output_tokens": 30000,
                "total_tokens": 40000,
                "total_cost": 1.00
            }
        }
    }


class PersonaDetailResponse(BaseModel):
    """Response model for detailed persona analytics"""
    persona: Optional[PersonaUsageItem] = Field(None, description="Basic persona information and usage statistics")
    
    # Time series data for usage trends
    daily_usage: List[DailyUsageItem] = Field(
        default_factory=list,
        description="Daily usage statistics"
    )
    
    # Request statistics
    request_count_by_model: Dict[str, int] = Field(
        default_factory=dict,
        description="Request counts by model"
    )
    request_count_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Request counts by status"
    )
    
    # Token usage statistics
    token_usage_by_model: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Token usage by model"
    )
    
    # User statistics (if not restricted to a single user)
    top_users: List[UserUsageSummary] = Field(
        default_factory=list,
        description="Top users of this persona"
    )
    
    period_start: Optional[datetime] = Field(None, description="Start of period", examples=["2025-06-01T00:00:00Z"])
    period_end: Optional[datetime] = Field(None, description="End of period", examples=["2025-06-07T23:59:59Z"])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "persona": {
                    "persona_id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "Customer Support Agent",
                    "description": "A helpful customer support agent",
                    "user_id": "user123",
                    "request_count": 150,
                    "success_count": 145,
                    "failure_count": 5,
                    "success_rate": 96.7,
                    "input_tokens": 15000,
                    "output_tokens": 45000,
                    "total_tokens": 60000,
                    "total_cost": 1.25,
                    "avg_response_time": 1.5,
                    "last_used_at": "2025-06-01T12:34:56Z",
                    "models_used": ["gpt-4o", "gpt-4o-mini"],
                    "is_active": True
                },
                "daily_usage": [
                    {"date": "2025-06-01", "request_count": 25, "success_count": 24, "failure_count": 1, "total_tokens": 10000, "total_cost": 0.25},
                    {"date": "2025-06-02", "request_count": 30, "success_count": 29, "failure_count": 1, "total_tokens": 12000, "total_cost": 0.30}
                ],
                "request_count_by_model": {
                    "gpt-4o": 100,
                    "gpt-4o-mini": 50
                },
                "request_count_by_status": {
                    "completed": 145,
                    "failed": 5
                },
                "token_usage_by_model": {
                    "gpt-4o": {
                        "input_tokens": 10000,
                        "output_tokens": 30000,
                        "total_tokens": 40000,
                        "total_cost": 1.00
                    },
                    "gpt-4o-mini": {
                        "input_tokens": 5000,
                        "output_tokens": 15000,
                        "total_tokens": 20000,
                        "total_cost": 0.25
                    }
                },
                "top_users": [
                    {"user_id": "user123", "request_count": 75, "total_tokens": 30000, "total_cost": 0.75},
                    {"user_id": "user456", "request_count": 50, "total_tokens": 20000, "total_cost": 0.50}
                ],
                "period_start": "2025-06-01T00:00:00Z",
                "period_end": "2025-06-07T23:59:59Z"
            }
        }
    }
