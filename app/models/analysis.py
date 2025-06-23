"""Pydantic models for analysis feature"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class CategoryDefinition(BaseModel):
    """Definition of a category for analysis (e.g., intent, sentiment)"""
    name: str = Field(..., description="Name of the category")
    description: str = Field(..., description="Description of what this category represents")
    examples: Optional[List[str]] = Field(default_factory=list, description="Example phrases for this category")


class AnalysisConfigData(BaseModel):
    """Configuration data for analysis"""
    analysis_type: str = Field(..., description="Type of analysis (intent, sentiment, topic, etc.)")
    categories: List[CategoryDefinition] = Field(..., description="Categories to analyze")
    model: str = Field(default="gpt-4o-mini", description="Model to use for analysis")
    temperature: float = Field(default=0.3, description="Temperature for the model")
    include_reasoning: bool = Field(default=True, description="Include reasoning in the response")
    include_confidence: bool = Field(default=True, description="Include confidence scores")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens for analysis")
    multi_label: bool = Field(default=False, description="Allow multiple categories to be selected")
    custom_prompt: Optional[str] = Field(default=None, description="Custom prompt template")
    additional_fields: Optional[Dict[str, Any]] = Field(default=None, description="Additional custom fields")


class AnalysisConfigCreate(BaseModel):
    """Request model for creating an analysis configuration"""
    name: str = Field(..., description="Name of the configuration")
    description: Optional[str] = Field(default=None, description="Description of the configuration")
    config: AnalysisConfigData = Field(..., description="Configuration data")


class AnalysisConfigUpdate(BaseModel):
    """Request model for updating an analysis configuration"""
    name: Optional[str] = Field(default=None, description="New name")
    description: Optional[str] = Field(default=None, description="New description")
    config: Optional[AnalysisConfigData] = Field(default=None, description="New configuration data")
    is_active: Optional[bool] = Field(default=None, description="Active status")


class AnalysisConfig(BaseModel):
    """Response model for analysis configuration"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str]
    config: Dict[str, Any]  # Will be AnalysisConfigData when serialized
    is_active: bool
    created_by: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class AnalysisConfigList(BaseModel):
    """Response model for listing analysis configurations"""
    items: List[AnalysisConfig]
    total: int
    page: int = 1
    page_size: int = 50


class AnalysisRequest(BaseModel):
    """Request model for performing analysis"""
    id: str = Field(..., description="Request ID or Response ID to analyze")
    config_id: Optional[uuid.UUID] = Field(default=None, description="ID of saved configuration to use")
    config: Optional[AnalysisConfigData] = Field(default=None, description="Inline configuration (if not using config_id)")
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Override specific config fields")


class CategoryResult(BaseModel):
    """Result for a single category"""
    name: str
    confidence: float
    reasoning: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response model for analysis results"""
    request_id: str
    response_id: Optional[str]
    analysis_type: str
    primary_category: Optional[str] = Field(default=None, description="Primary detected category (for single-label)")
    categories: List[CategoryResult] = Field(default_factory=list, description="All analyzed categories with scores")
    confidence: Optional[float] = Field(default=None, description="Overall confidence")
    reasoning: Optional[str] = Field(default=None, description="Overall reasoning")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    analyzed_at: datetime
    model_used: str
    tokens_used: int
    cost_usd: float
    cached: bool = Field(default=False, description="Whether this result was cached")


class AnalysisResult(BaseModel):
    """Database model for analysis results"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    request_id: uuid.UUID
    analysis_config_id: Optional[uuid.UUID]
    config_snapshot: Dict[str, Any]
    analysis_type: str
    results: Dict[str, Any]
    model_used: str
    tokens_used: int
    cost_usd: float
    created_at: datetime


# Error models
class AnalysisError(BaseModel):
    """Error response for analysis endpoints"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
