"""Configuration management for the OpenAI Inference Proxy"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/openai_proxy",
        description="PostgreSQL connection URL"
    )
    
    # Security
    jwt_secret_key: str = Field(
        ...,
        description="Secret key for JWT token validation"
    )
    encryption_key: str = Field(
        ...,
        description="Fernet key for encrypting API keys"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithm for JWT encoding/decoding"
    )
    jwt_expiration_days: int = Field(
        default=365,
        description="JWT token expiration in days"
    )
    
    # OpenAI
    openai_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_timeout: int = Field(
        default=600,
        description="Timeout for OpenAI API requests in seconds"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        # Handle None or empty values
        if v is None or v == "":
            return ["http://localhost:3000", "http://localhost:8080"]
        
        # If it's already a list, return it
        if isinstance(v, list):
            return v
        
        # If it's a string, try to parse it
        if isinstance(v, str):
            # First check if it looks like JSON
            if v.strip().startswith("["):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            
            # Otherwise treat as comma-separated
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        
        return v
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Settings
    api_prefix: str = Field(default="/v1", description="API route prefix")
    project_name: str = Field(
        default="OpenAI Inference Proxy",
        description="Project name for documentation"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=100,
        description="Number of requests allowed per time window"
    )
    rate_limit_window: int = Field(
        default=60,
        description="Time window for rate limiting in seconds"
    )
    
    class Config:
        # Only read .env file if not in Docker
        env_file = ".env" if not os.getenv("DOCKER_ENV") else None
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create global settings instance
settings = Settings()


# Validate critical settings at startup
def validate_settings():
    """Validate that all critical settings are properly configured"""
    if settings.jwt_secret_key == "your-secret-key-here-change-in-production":
        raise ValueError(
            "JWT_SECRET_KEY must be changed from default value in production"
        )
    
    if settings.encryption_key == "generate-fernet-key-for-production":
        raise ValueError(
            "ENCRYPTION_KEY must be changed from default value in production"
        )
    
    # Validate Fernet key format
    try:
        from cryptography.fernet import Fernet
        Fernet(settings.encryption_key.encode())
    except Exception as e:
        raise ValueError(f"Invalid ENCRYPTION_KEY format: {e}")
