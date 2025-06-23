"""Main FastAPI application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys

from app.config import settings, validate_settings
from app.core import init_db, close_db
from app.api import (
    responses_router, users_router, api_keys_router, 
    analytics_router, personas_router, analysis_router, 
    analysis_configs_router
)
from app.models.requests import ErrorResponse, ErrorDetail

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting OpenAI Inference Proxy...")
    
    # Validate settings
    try:
        validate_settings()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Initialize database
    await init_db()
    
    yield
    
    # Cleanup
    logger.info("Shutting down OpenAI Inference Proxy...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="""
    A secure proxy for OpenAI's Responses API with JWT authentication, usage tracking, response rating, and conversation analysis.
    
    ## Features
    
    - **JWT Authentication**: Secure access to the API
    - **User Management**: Create and manage users
    - **API Key Management**: Create and manage API keys
    - **Usage Tracking**: Track token usage and costs
    - **Response Rating**: Rate responses for quality tracking
    - **Conversation Analysis**: Analyze conversations for intents, sentiments, topics, and custom classifications
    - **Analysis Configurations**: Create reusable analysis templates for consistent classification
    
    ## Authentication
    
    All endpoints require JWT authentication via the Authorization header.
    """,
    version="0.1.0",
    openapi_tags=[
        {
            "name": "responses",
            "description": "OpenAI Responses API proxy endpoints for forwarding requests to OpenAI"
        },
        {
            "name": "users",
            "description": "User management endpoints for creating and managing users"
        },
        {
            "name": "api_keys",
            "description": "API key management endpoints for creating and managing API keys"
        },
        {
            "name": "analytics",
            "description": "Analytics endpoints for usage statistics and insights"
        },
        {
            "name": "personas",
            "description": "Persona management endpoints for creating and managing system prompts"
        },
        {
            "name": "analysis",
            "description": "Conversation analysis endpoints for intent detection, sentiment analysis, and custom classifications"
        },
        {
            "name": "analysis-configs",
            "description": "Analysis configuration management endpoints for creating reusable analysis templates"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Session-ID"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            type="internal_error",
            message="An unexpected error occurred",
            code="INTERNAL_ERROR"
        )
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.project_name,
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs"
    }


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": "0.1.0"
    }


# Include routers
app.include_router(
    responses_router,
    prefix=settings.api_prefix
)

app.include_router(
    users_router,
    prefix=f"{settings.api_prefix}/api"
)

app.include_router(
    api_keys_router,
    prefix=f"{settings.api_prefix}/api"
)

app.include_router(
    analytics_router,
    prefix=settings.api_prefix
)

app.include_router(
    personas_router,
    prefix=settings.api_prefix
)

app.include_router(
    analysis_configs_router,
    prefix=settings.api_prefix
)

app.include_router(
    analysis_router,
    prefix=settings.api_prefix
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
