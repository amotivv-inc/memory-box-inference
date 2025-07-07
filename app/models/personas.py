"""Pydantic models for persona management"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class PersonaCreate(BaseModel):
    """Request model for creating a persona"""
    name: str = Field(
        ..., 
        description="Name of the persona",
        examples=["Customer Support Agent"]
    )
    description: Optional[str] = Field(
        None, 
        description="Optional description of the persona",
        examples=["A helpful customer support agent that assists users with their inquiries"]
    )
    content: str = Field(
        ..., 
        description="System prompt content",
        examples=["You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful."]
    )
    user_id: Optional[str] = Field(
        None, 
        description="Optional user ID to restrict the persona to a specific user",
        examples=["user-123"]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Flexible metadata for tagging, versioning, and organizational schemes",
        examples=[{
            "tags": ["prod", "approved"],
            "version": "2.0.0",
            "status": "production",
            "department": "customer_success"
        }]
    )


class PersonaUpdate(BaseModel):
    """Request model for updating a persona"""
    name: Optional[str] = Field(
        None, 
        description="Name of the persona",
        examples=["Updated Customer Support Agent"]
    )
    description: Optional[str] = Field(
        None, 
        description="Optional description of the persona",
        examples=["An updated description for the customer support agent"]
    )
    content: Optional[str] = Field(
        None, 
        description="System prompt content",
        examples=["Updated system prompt content"]
    )
    user_id: Optional[str] = Field(
        None, 
        description="Optional user ID to restrict the persona to a specific user",
        examples=["user-456"]
    )
    is_active: Optional[bool] = Field(
        None, 
        description="Whether the persona is active",
        examples=[True]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Flexible metadata for tagging, versioning, and organizational schemes",
        examples=[{
            "tags": ["prod", "approved", "tested"],
            "version": "2.1.0",
            "last_tested": "2025-01-15T14:30:00Z"
        }]
    )


class PersonaResponse(BaseModel):
    """Response model for persona operations"""
    id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    organization_id: str = Field(
        ...,
        examples=["123e4567-e89b-12d3-a456-426614174001"]
    )
    user_id: Optional[str] = Field(
        None,
        examples=["user-123"]
    )
    name: str = Field(
        ...,
        examples=["Customer Support Agent"]
    )
    description: Optional[str] = Field(
        None,
        examples=["A helpful customer support agent that assists users with their inquiries"]
    )
    content: str = Field(
        ...,
        examples=["You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful."]
    )
    is_active: bool = Field(
        ...,
        examples=[True]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Flexible metadata for tagging, versioning, and organizational schemes",
        examples=[{
            "tags": ["prod", "approved"],
            "version": "2.0.0",
            "status": "production"
        }]
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
                "user_id": "user-123",
                "name": "Customer Support Agent",
                "description": "A helpful customer support agent that assists users with their inquiries",
                "content": "You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful.",
                "is_active": True,
                "metadata": {
                    "tags": ["prod", "approved"],
                    "version": "2.0.0",
                    "status": "production",
                    "department": "customer_success"
                },
                "created_at": "2025-05-29T16:00:00.000Z",
                "updated_at": "2025-05-29T16:00:00.000Z"
            }
        }
    }


class PersonaList(BaseModel):
    """Response model for listing personas"""
    personas: List[PersonaResponse]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "personas": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": "user-123",
                        "name": "Customer Support Agent",
                        "description": "A helpful customer support agent that assists users with their inquiries",
                        "content": "You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful.",
                        "is_active": True,
                        "metadata": {
                            "tags": ["prod", "approved"],
                            "version": "2.0.0",
                            "status": "production",
                            "department": "customer_success"
                        },
                        "created_at": "2025-05-29T16:00:00.000Z",
                        "updated_at": "2025-05-29T16:00:00.000Z"
                    },
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174002",
                        "organization_id": "123e4567-e89b-12d3-a456-426614174001",
                        "user_id": None,
                        "name": "Technical Support Agent",
                        "description": "A technical support agent that helps users with technical issues",
                        "content": "You are a technical support agent for Acme Inc. You should provide detailed technical assistance.",
                        "is_active": True,
                        "metadata": {
                            "tags": ["dev", "testing"],
                            "version": "1.5.0",
                            "status": "development"
                        },
                        "created_at": "2025-05-29T16:30:00.000Z",
                        "updated_at": "2025-05-29T16:30:00.000Z"
                    }
                ]
            }
        }
    }
