"""SQLAlchemy database models"""

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, 
    Text, DECIMAL, CheckConstraint, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Organization(Base):
    """Organizations that own API keys"""
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    personas = relationship("Persona", back_populates="organization", cascade="all, delete-orphan")
    analysis_configs = relationship("AnalysisConfig", back_populates="organization", cascade="all, delete-orphan")


class APIKey(Base):
    """Mapping between synthetic and real OpenAI API keys"""
    __tablename__ = "api_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # New field
    synthetic_key = Column(String(255), unique=True, nullable=False, index=True)
    openai_api_key = Column(Text, nullable=False)  # Encrypted
    is_active = Column(Boolean, default=True)
    name = Column(String(255), nullable=True)  # Optional name for the key
    description = Column(Text, nullable=True)  # Optional description
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")  # New relationship
    requests = relationship("Request", back_populates="api_key")


class User(Base):
    """Users within organizations"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String(255), nullable=False)  # External user ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    personas = relationship("Persona", back_populates="user")
    created_analysis_configs = relationship("AnalysisConfig", back_populates="created_by_user")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'user_id', name='_org_user_uc'),
    )


class Session(Base):
    """User sessions for grouping requests"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    requests = relationship("Request", back_populates="session", cascade="all, delete-orphan")


class Request(Base):
    """Individual API requests"""
    __tablename__ = "requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(255), unique=True, nullable=False, index=True)
    response_id = Column(String(255), nullable=True, index=True)  # OpenAI's response ID
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=False)
    persona_id = Column(UUID(as_uuid=True), ForeignKey("personas.id"), nullable=True)  # Reference to persona
    model = Column(String(100), nullable=False)
    request_payload = Column(JSON, nullable=False)
    response_payload = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False)  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)
    rating_timestamp = Column(DateTime(timezone=True), nullable=True)
    rating_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="requests")
    user = relationship("User", back_populates="requests")
    api_key = relationship("APIKey", back_populates="requests")
    persona = relationship("Persona", back_populates="requests")
    usage_logs = relationship("UsageLog", back_populates="request", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="request", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('rating IN (-1, 0, 1)', name='check_rating_values'),
    )


class UsageLog(Base):
    """Token usage and cost tracking"""
    __tablename__ = "usage_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    reasoning_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    model = Column(String(100), nullable=True)
    cost_usd = Column(DECIMAL(10, 6), nullable=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("Request", back_populates="usage_logs")


class Persona(Base):
    """Stored system prompts (personas) for OpenAI requests"""
    __tablename__ = "personas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Optional user restriction
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # The actual system prompt content
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="personas")
    user = relationship("User", back_populates="personas")
    requests = relationship("Request", back_populates="persona")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='_org_persona_name_uc'),
    )


class AnalysisConfig(Base):
    """Analysis configurations for conversation analysis"""
    __tablename__ = "analysis_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="analysis_configs")
    created_by_user = relationship("User", back_populates="created_analysis_configs")
    analysis_results = relationship("AnalysisResult", back_populates="analysis_config")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('organization_id', 'name', name='_org_analysis_config_name_uc'),
    )


class AnalysisResult(Base):
    """Results of analysis performed on requests/responses"""
    __tablename__ = "analysis_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("requests.id"), nullable=False)
    analysis_config_id = Column(UUID(as_uuid=True), ForeignKey("analysis_configs.id"), nullable=True)
    config_snapshot = Column(JSON, nullable=False)
    analysis_type = Column(String(100), nullable=True)
    results = Column(JSON, nullable=False)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(DECIMAL(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("Request", back_populates="analysis_results")
    analysis_config = relationship("AnalysisConfig", back_populates="analysis_results")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('request_id', 'analysis_config_id', name='_request_config_uc'),
    )
