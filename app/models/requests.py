"""Pydantic models for API requests and responses"""

from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


# OpenAI Responses API Models

class ResponsesInput(BaseModel):
    """Input model for OpenAI Responses API"""
    input: Union[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Text, image, or file inputs to the model",
        examples=["Tell me about artificial intelligence"]
    )
    model: str = Field(
        ...,
        description="Model ID like gpt-4o or o3",
        examples=["gpt-4o"]
    )
    background: Optional[bool] = Field(
        default=False,
        description="Whether to run in background"
    )
    include: Optional[List[str]] = Field(
        default=None,
        description="Additional output data to include"
    )
    instructions: Optional[str] = Field(
        default=None,
        description="System message",
        examples=["You are a helpful AI assistant."]
    )
    max_output_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens for response",
        examples=[1000]
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Key-value pairs for metadata"
    )
    parallel_tool_calls: Optional[bool] = Field(
        default=True,
        description="Allow parallel tool calls"
    )
    previous_response_id: Optional[str] = Field(
        default=None,
        description="ID of previous response for conversation"
    )
    reasoning: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for reasoning models"
    )
    service_tier: Optional[Literal["auto", "default", "flex"]] = Field(
        default="auto",
        description="Latency tier for processing"
    )
    store: Optional[bool] = Field(
        default=True,
        description="Whether to store the response"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Whether to stream the response",
        examples=[True]
    )
    temperature: Optional[float] = Field(
        default=1.0,
        ge=0,
        le=2,
        description="Sampling temperature",
        examples=[0.7]
    )
    text: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for text response"
    )
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(
        default="auto",
        description="How to select tools"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tools the model may call"
    )
    top_p: Optional[float] = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Nucleus sampling parameter"
    )
    truncation: Optional[Literal["auto", "disabled"]] = Field(
        default="disabled",
        description="Truncation strategy"
    )
    user: Optional[str] = Field(
        default=None,
        description="End-user identifier"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "input": "Tell me about artificial intelligence",
                "model": "gpt-4o",
                "stream": True,
                "temperature": 0.7,
                "max_output_tokens": 1000,
                "instructions": "You are a helpful AI assistant."
            }
        }
    }


# Rating Models

class RatingRequest(BaseModel):
    """Request model for rating a response"""
    rating: Literal[-1, 1] = Field(
        ...,
        description="Rating value: -1 for downvote, 1 for upvote",
        examples=[1]
    )
    feedback: Optional[str] = Field(
        default=None,
        description="Optional feedback text",
        examples=["This response was very helpful and accurate."]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rating": 1,
                "feedback": "This response was very helpful and accurate."
            }
        }
    }


class RatingResponse(BaseModel):
    """Response model for rating confirmation"""
    request_id: str = Field(
        ...,
        examples=["req_1234567890abcdef"]
    )
    rating: int = Field(
        ...,
        examples=[1]
    )
    feedback: Optional[str] = Field(
        default=None,
        examples=["This response was very helpful and accurate."]
    )
    rated_at: datetime = Field(
        ...,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "req_1234567890abcdef",
                "rating": 1,
                "feedback": "This response was very helpful and accurate.",
                "rated_at": "2025-05-29T16:00:00.000Z"
            }
        }
    }


# Error Models

class ErrorDetail(BaseModel):
    """Error detail model"""
    type: str = Field(
        ...,
        examples=["api_error"]
    )
    message: str = Field(
        ...,
        examples=["Invalid API key provided"]
    )
    code: str = Field(
        ...,
        examples=["INVALID_API_KEY"]
    )
    request_id: Optional[str] = Field(
        default=None,
        examples=["req_1234567890abcdef"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "api_error",
                "message": "Invalid API key provided",
                "code": "INVALID_API_KEY",
                "request_id": "req_1234567890abcdef"
            }
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": {
                    "type": "api_error",
                    "message": "Invalid API key provided",
                    "code": "INVALID_API_KEY",
                    "request_id": "req_1234567890abcdef"
                }
            }
        }
    }


# Usage Models

class UsageInfo(BaseModel):
    """Token usage information"""
    input_tokens: int = Field(
        ...,
        examples=[50]
    )
    output_tokens: int = Field(
        ...,
        examples=[250]
    )
    reasoning_tokens: Optional[int] = Field(
        default=0,
        examples=[0]
    )
    total_tokens: int = Field(
        ...,
        examples=[300]
    )
    cost_usd: Optional[float] = Field(
        default=None,
        examples=[0.0075]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "input_tokens": 50,
                "output_tokens": 250,
                "reasoning_tokens": 0,
                "total_tokens": 300,
                "cost_usd": 0.0075
            }
        }
    }


# Session Models

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str = Field(
        ...,
        examples=["sess_1234567890abcdef"]
    )
    user_id: str = Field(
        ...,
        examples=["external-user-123"]
    )
    started_at: datetime = Field(
        ...,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    request_count: int = Field(
        default=0,
        examples=[5]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "sess_1234567890abcdef",
                "user_id": "external-user-123",
                "started_at": "2025-05-29T16:00:00.000Z",
                "request_count": 5
            }
        }
    }


# Health Check

class HealthResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"] = Field(
        default="healthy",
        examples=["healthy"]
    )
    message: str = Field(
        default="Service is operational",
        examples=["OpenAI API is responding correctly"]
    )
    openai_status: Literal["operational", "error", "unknown"] = Field(
        default="unknown",
        examples=["operational"]
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    version: str = Field(
        default="0.1.0",
        examples=["0.1.0"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "message": "OpenAI API is responding correctly",
                "openai_status": "operational",
                "timestamp": "2025-05-29T16:00:00.000Z",
                "version": "0.1.0"
            }
        }
    }


# User Management Models

class UserCreate(BaseModel):
    """Request model for creating a user"""
    user_id: str = Field(
        ..., 
        description="External user ID",
        examples=["external-user-123"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "external-user-123"
            }
        }
    }


class UserResponse(BaseModel):
    """Response model for user operations"""
    id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    organization_id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
    user_id: str = Field(
        ...,
        examples=["external-user-123"]
    )
    created_at: datetime = Field(
        ...,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "external-user-123",
                "created_at": "2025-05-29T16:00:00.000Z"
            }
        }
    }


class UserList(BaseModel):
    """Response model for listing users"""
    users: List[UserResponse]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "external-user-123",
                        "created_at": "2025-05-29T16:00:00.000Z"
                    },
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "external-user-456",
                        "created_at": "2025-05-29T16:30:00.000Z"
                    }
                ]
            }
        }
    }


# API Key Management Models

class APIKeyCreate(BaseModel):
    """Request model for creating an API key"""
    openai_api_key: str = Field(
        ..., 
        description="OpenAI API key to encrypt",
        examples=["sk-your-openai-key"]
    )
    user_id: Optional[str] = Field(
        default=None, 
        description="User ID to associate with the key",
        examples=["user-uuid"]
    )
    name: Optional[str] = Field(
        default=None, 
        description="Name for the key",
        examples=["Production API Key"]
    )
    description: Optional[str] = Field(
        default=None, 
        description="Description for the key",
        examples=["API key for production environment"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "openai_api_key": "sk-your-openai-key",
                "user_id": "user-uuid",
                "name": "Production API Key",
                "description": "API key for production environment"
            }
        }
    }


class APIKeyUpdate(BaseModel):
    """Request model for updating an API key"""
    is_active: Optional[bool] = Field(
        default=None, 
        description="Whether the key is active",
        examples=[True]
    )
    user_id: Optional[str] = Field(
        default=None, 
        description="User ID to associate with the key",
        examples=["user-uuid"]
    )
    name: Optional[str] = Field(
        default=None, 
        description="Name for the key",
        examples=["Updated Key Name"]
    )
    description: Optional[str] = Field(
        default=None, 
        description="Description for the key",
        examples=["Updated description"]
    )
    openai_api_key: Optional[str] = Field(
        default=None, 
        description="New OpenAI API key",
        examples=["sk-new-openai-key"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "is_active": True,
                "user_id": "user-uuid",
                "name": "Updated Key Name",
                "description": "Updated description",
                "openai_api_key": "sk-new-openai-key"
            }
        }
    }


class APIKeyResponse(BaseModel):
    """Response model for API key operations"""
    id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    organization_id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
    user_id: Optional[str] = Field(
        default=None,
        examples=["user-uuid"]
    )
    synthetic_key: str = Field(
        ...,
        examples=["oip_1234567890abcdef"]
    )
    is_active: bool = Field(
        ...,
        examples=[True]
    )
    name: Optional[str] = Field(
        default=None,
        examples=["Production API Key"]
    )
    description: Optional[str] = Field(
        default=None,
        examples=["API key for production environment"]
    )
    created_at: datetime = Field(
        ...,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    updated_at: datetime = Field(
        ...,
        examples=["2025-05-29T16:00:00.000Z"]
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_id": "user-uuid",
                "synthetic_key": "oip_1234567890abcdef",
                "is_active": True,
                "name": "Production API Key",
                "description": "API key for production environment",
                "created_at": "2025-05-29T16:00:00.000Z",
                "updated_at": "2025-05-29T16:00:00.000Z"
            }
        }
    }


class APIKeyList(BaseModel):
    """Response model for listing API keys"""
    api_keys: List[APIKeyResponse]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "api_keys": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "user-uuid",
                        "synthetic_key": "oip_1234567890abcdef",
                        "is_active": True,
                        "name": "Production API Key",
                        "description": "API key for production environment",
                        "created_at": "2025-05-29T16:00:00.000Z",
                        "updated_at": "2025-05-29T16:00:00.000Z"
                    },
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "user-uuid",
                        "synthetic_key": "oip_abcdef1234567890",
                        "is_active": False,
                        "name": "Development API Key",
                        "description": "API key for development environment",
                        "created_at": "2025-05-29T15:00:00.000Z",
                        "updated_at": "2025-05-29T16:30:00.000Z"
                    }
                ]
            }
        }
    }
