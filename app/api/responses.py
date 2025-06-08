"""OpenAI Responses API proxy endpoints"""

from fastapi import APIRouter, Depends, HTTPException, Header, Response, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, Any, Optional
import json
import uuid
from datetime import datetime

from app.core import get_db, get_current_organization
from app.core.openai_client import openai_client
from app.core.security import decrypt_api_key
from app.models.requests import (
    ResponsesInput, RatingRequest, RatingResponse,
    ErrorResponse, ErrorDetail, HealthResponse
)
from app.models.database import Request as RequestModel, APIKey
from app.services import KeyMapperService, SessionManagerService, UsageLoggerService, PersonaService
from app.utils import StreamingResponseHandler
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/responses", tags=["responses"])


@router.post(
    "",
    summary="Proxy a request to OpenAI's Responses API",
    description="""
    This endpoint forwards requests to OpenAI's Responses API, handling authentication,
    session management, usage tracking, and response formatting.
    
    This endpoint:
    1. Validates JWT authentication
    2. Maps organization to OpenAI API key
    3. Creates/manages sessions
    4. Forwards request to OpenAI
    5. Logs usage and costs
    6. Returns response (streaming or non-streaming)
    """,
    response_description="""
    For streaming requests: Server-Sent Events (SSE) stream with OpenAI responses
    For non-streaming requests: JSON response from OpenAI
    
    Headers in response:
    - X-Request-ID: Unique ID for the request
    - X-Session-ID: Session ID for the request
    """,
    responses={
        200: {
            "description": "Successful response from OpenAI",
            "content": {
                "application/json": {
                    "example": {
                        "id": "resp_abc123",
                        "content": [{"text": "This is a response from the AI model."}],
                        "usage": {"input_tokens": 10, "output_tokens": 50, "total_tokens": 60}
                    }
                },
                "text/event-stream": {
                    "description": "Server-Sent Events stream for streaming responses"
                }
            }
        },
        400: {
            "description": "Bad Request - If request validation fails",
            "model": ErrorResponse
        },
        401: {
            "description": "Unauthorized - If JWT authentication fails",
            "model": ErrorResponse
        },
        403: {
            "description": "Forbidden - If no active API key is found for the organization",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal Server Error - If an unexpected error occurs",
            "model": ErrorResponse
        }
    }
)
async def create_response(
    request_data: ResponsesInput,
    request: Request,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization),
    x_user_id: str = Header(..., description="User ID for tracking"),
    x_session_id: Optional[str] = Header(None, description="Optional session ID")
):
    """Proxy a request to OpenAI's Responses API."""
    try:
        # Initialize services
        key_mapper = KeyMapperService(db)
        session_manager = SessionManagerService(db)
        usage_logger = UsageLoggerService(db)
        persona_service = PersonaService(db)
        
        # Get or create user first
        user = await session_manager.get_or_create_user(
            organization_id=organization["organization_id"],
            user_id=x_user_id
        )
        
        # Get appropriate API key for this user
        api_key_record = await key_mapper.get_api_key_for_request(
            organization_id=organization["organization_id"],
            user_id=str(user.id)
        )
        
        if not api_key_record:
            raise HTTPException(
                status_code=403,
                detail=f"No active API key found for user {x_user_id} or organization"
            )
        
        # Decrypt the OpenAI key
        openai_key = decrypt_api_key(api_key_record.openai_api_key)
        
        # Get or create session
        session = await session_manager.get_or_create_session(
            organization_id=organization["organization_id"],
            user_id=x_user_id,
            session_id=x_session_id
        )
        
        # Handle persona if specified
        persona_id = None
        if request_data.persona_id:
            try:
                persona = await persona_service.get_persona_for_request(
                    organization_id=organization["organization_id"],
                    persona_id=request_data.persona_id,
                    external_user_id=x_user_id
                )
                
                if not persona:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Persona with ID {request_data.persona_id} not found or not accessible"
                    )
                
                # Override instructions with persona content
                request_data.instructions = persona.content
                persona_id = str(persona.id)
                logger.info(f"Using persona {persona.name} for request")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid persona ID format: {request_data.persona_id}"
                )
        
        # Generate request ID
        request_id = f"req_{uuid.uuid4().hex}"
        
        # Create request record
        request_record = await usage_logger.create_request(
            request_id=request_id,
            session_id=session.id,
            user_id=session.user_id,
            api_key_id=api_key_record.id,
            model=request_data.model,
            request_payload=request_data.model_dump(),
            persona_id=persona_id
        )
        
        # Prepare request for OpenAI - exclude persona_id as it's not recognized by OpenAI
        openai_request = request_data.model_dump(exclude={"persona_id"} if request_data.persona_id else None, exclude_none=True)
        
        # Handle streaming vs non-streaming
        if request_data.stream:
            # Streaming response
            async def generate():
                try:
                    # Create streaming handler
                    handler = StreamingResponseHandler()
                    
                    # Get stream from OpenAI
                    openai_stream = openai_client.create_response(
                        api_key=openai_key,
                        request_data=openai_request,
                        stream=True
                    )
                    
                    # Process stream
                    async for chunk in handler.process_stream(
                        openai_stream,
                        request_id,
                        session.session_id
                    ):
                        yield chunk
                    
                    # Log usage after stream completes
                    if handler.error_data:
                        # If there's an error, mark the request as failed
                        await usage_logger.update_request_status(
                            request_id=request_id,
                            status="failed",
                            error_message=json.dumps(handler.error_data)
                        )
                    else:
                        # If there's no error, mark the request as completed regardless of usage data
                        if handler.usage_data:
                            # If we have usage data, log it
                            await usage_logger.log_usage(
                                request_id=request_id,
                                usage_data=handler.usage_data,
                                model=request_data.model
                            )
                    
                    # Store the response ID if available
                    if hasattr(handler, 'response_id') and handler.response_id:
                        # Use direct SQL UPDATE to ensure the response_id is saved
                        await db.execute(
                            update(RequestModel)
                            .where(RequestModel.request_id == request_id)
                            .values(response_id=handler.response_id)
                        )
                        await db.commit()
                        logger.info(f"Stored response ID {handler.response_id} for request {request_id}")
                    
                    # Always update status to completed if there's no error
                    await usage_logger.update_request_status(
                        request_id=request_id,
                        status="completed",
                        response_payload=handler.response_data
                    )
                    
                    await db.commit()
                    
                except Exception as e:
                    logger.error(f"Streaming error: {e}")
                    await usage_logger.update_request_status(
                        request_id=request_id,
                        status="failed",
                        error_message=str(e)
                    )
                    await db.commit()
                    
                    # Send error in SSE format
                    error_data = {
                        "error": {
                            "type": "streaming_error",
                            "message": str(e),
                            "code": "STREAM_ERROR",
                            "request_id": request_id
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            # Return streaming response with proper headers
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Request-ID": request_id,
                    "X-Session-ID": session.session_id,
                    "Access-Control-Expose-Headers": "X-Request-ID, X-Session-ID"
                }
            )
        
        else:
            # Non-streaming response
            try:
                # Get response from OpenAI
                response_generator = openai_client.create_response(
                    api_key=openai_key,
                    request_data=openai_request,
                    stream=False
                )
                
                # Get the single response
                response_text = None
                async for chunk in response_generator:
                    response_text = chunk
                    break
                
                # Parse response
                response_data = json.loads(response_text)
                
                # Check for error - only consider it an error if the error field exists AND is not null
                if "error" in response_data and response_data["error"] is not None:
                    await usage_logger.update_request_status(
                        request_id=request_id,
                        status="failed",
                        error_message=json.dumps(response_data["error"])
                    )
                    await db.commit()
                    
                    return Response(
                        content=response_text,
                        media_type="application/json",
                        status_code=400,
                        headers={
                            "X-Request-ID": request_id,
                            "X-Session-ID": session.session_id
                        }
                    )
                
                # Store the response ID if available
                response_id = response_data.get("id")
                if response_id:
                    # Use direct SQL UPDATE to ensure the response_id is saved
                    await db.execute(
                        update(RequestModel)
                        .where(RequestModel.request_id == request_id)
                        .values(response_id=response_id)
                    )
                    await db.commit()
                    logger.info(f"Stored response ID {response_id} for request {request_id}")
                
                # Log usage
                if "usage" in response_data:
                    await usage_logger.log_usage(
                        request_id=request_id,
                        usage_data=response_data["usage"],
                        model=request_data.model
                    )
                
                # Update request status
                await usage_logger.update_request_status(
                    request_id=request_id,
                    status="completed",
                    response_payload=response_data
                )
                
                await db.commit()
                
                # Return response with custom headers
                return Response(
                    content=response_text,
                    media_type="application/json",
                    status_code=200,  # Changed from 400 to 200 for successful responses
                    headers={
                        "X-Request-ID": request_id,
                        "X-Session-ID": session.session_id,
                        "Access-Control-Expose-Headers": "X-Request-ID, X-Session-ID"
                    }
                )
                
            except Exception as e:
                logger.error(f"Non-streaming error: {e}")
                await usage_logger.update_request_status(
                    request_id=request_id,
                    status="failed",
                    error_message=str(e)
                )
                await db.commit()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error processing request: {str(e)}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/health", 
    response_model=HealthResponse,
    summary="Health check for OpenAI API connectivity",
    description="""
    This endpoint performs a minimal request to OpenAI to verify that the API
    is accessible and responding correctly.
    """,
    response_description="""
    HealthResponse object with status, message, OpenAI status, timestamp, and version
    
    Possible status values:
    - "healthy": API is responding correctly
    - "degraded": API is accessible but returning errors
    - "unhealthy": API is not accessible
    """,
    responses={
        200: {
            "description": "Health check response",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "message": "OpenAI API is responding correctly",
                        "openai_status": "operational",
                        "timestamp": "2025-05-29T16:00:00.000Z",
                        "version": "0.1.0"
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized - If JWT authentication fails",
            "model": ErrorResponse
        },
        403: {
            "description": "Forbidden - If organization doesn't have permission",
            "model": ErrorResponse
        }
    }
)
async def health_check(
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Health check endpoint that verifies OpenAI API connectivity."""
    try:
        # Get OpenAI API key
        key_mapper = KeyMapperService(db)
        openai_key = await key_mapper.get_openai_key(organization["organization_id"])
        
        if not openai_key:
            return HealthResponse(
                status="degraded",
                message="No active API key found for organization",
                openai_status="unknown"
            )
        
        # Make a minimal request to OpenAI that matches the API documentation
        test_request = {
            "model": "gpt-4o-mini",  # Required: Model ID
            "input": "Hello",         # Required: Text input
            "max_output_tokens": 16,  # Optional: Minimum allowed value is 16
            "temperature": 0.0        # Optional: Deterministic output
        }
        
        try:
            # Try to get a response from OpenAI
            response_generator = openai_client.create_response(
                api_key=openai_key,
                request_data=test_request,
                stream=False
            )
            
            # Get the response
            response_text = None
            async for chunk in response_generator:
                response_text = chunk
                break
            
            if not response_text:
                return HealthResponse(
                    status="unhealthy",
                    message="No response received from OpenAI API",
                    openai_status="unknown"
                )
            
            # Log the raw response for debugging
            logger.info(f"OpenAI API raw response: {response_text}")
            
            # Parse response
            try:
                response_data = json.loads(response_text)
                # Log the parsed response for debugging
                logger.info(f"OpenAI API parsed response: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {response_text}")
                return HealthResponse(
                    status="degraded",
                    message=f"Invalid JSON response from OpenAI API: {response_text[:100]}...",
                    openai_status="error"
                )
            
            # Check for error - only consider it an error if the error field exists AND is not null
            if "error" in response_data and response_data["error"] is not None:
                error_message = "Unknown error"
                
                # Log the error details
                logger.error(f"OpenAI API error details: {json.dumps(response_data.get('error'), indent=2)}")
                
                # Handle different error formats
                if isinstance(response_data.get("error"), dict):
                    error_message = response_data["error"].get("message", "Unknown error")
                elif isinstance(response_data.get("error"), str):
                    error_message = response_data["error"]
                
                return HealthResponse(
                    status="degraded",
                    message=f"OpenAI API error: {error_message}",
                    openai_status="error"
                )
            
            # Success
            return HealthResponse(
                status="healthy",
                message="OpenAI API is responding correctly",
                openai_status="operational",
                timestamp=datetime.utcnow(),
                version="0.1.0"
            )
            
        except Exception as e:
            logger.error(f"OpenAI request error: {e}")
            return HealthResponse(
                status="degraded",
                message=f"Error making request to OpenAI API: {str(e)}",
                openai_status="error"
            )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"Error checking OpenAI API: {str(e)}",
            openai_status="unknown"
        )


@router.get(
    "/{response_id}",
    summary="Get a response by ID from OpenAI",
    description="""
    This endpoint retrieves a specific response from OpenAI by its ID.
    """,
    response_description="JSON response from OpenAI containing the response data",
    responses={
        200: {
            "description": "Successful response retrieval",
            "content": {
                "application/json": {
                    "example": {
                        "id": "resp_abc123",
                        "content": [{"text": "This is a response from the AI model."}],
                        "usage": {"input_tokens": 10, "output_tokens": 50, "total_tokens": 60}
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - If response ID format is invalid",
            "model": ErrorResponse
        },
        401: {
            "description": "Unauthorized - If JWT authentication fails",
            "model": ErrorResponse
        },
        403: {
            "description": "Forbidden - If no active API key is found for the organization",
            "model": ErrorResponse
        },
        404: {
            "description": "Not Found - If response doesn't exist",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal Server Error - If an unexpected error occurs",
            "model": ErrorResponse
        }
    }
)
async def get_response(
    response_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Get a response by ID from OpenAI."""
    try:
        # Get OpenAI API key
        key_mapper = KeyMapperService(db)
        openai_key = await key_mapper.get_openai_key(organization["organization_id"])
        
        if not openai_key:
            raise HTTPException(
                status_code=403,
                detail="No active API key found for organization"
            )
        
        # Get response from OpenAI
        response_data = await openai_client.get_response(openai_key, response_id)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving response: {str(e)}"
        )


@router.post(
    "/{id}/rate",
    response_model=RatingResponse,
    summary="Rate a response",
    description="""
    This endpoint allows users to rate a response with a thumbs up (1) or thumbs down (-1)
    and optionally provide feedback text.
    
    The ID can be either:
    - A request ID (starting with 'req_')
    - A response ID (starting with 'resp_')
    """,
    response_description="RatingResponse object with request ID, rating, feedback, and timestamp",
    responses={
        200: {
            "description": "Rating successfully recorded",
            "model": RatingResponse,
            "content": {
                "application/json": {
                    "example": {
                        "request_id": "req_1234567890abcdef",
                        "rating": 1,
                        "feedback": "This response was very helpful",
                        "rated_at": "2025-05-29T16:00:00.000Z"
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - If rating data is invalid",
            "model": ErrorResponse
        },
        401: {
            "description": "Unauthorized - If JWT authentication fails",
            "model": ErrorResponse
        },
        403: {
            "description": "Forbidden - If organization doesn't have permission to rate the response",
            "model": ErrorResponse
        },
        404: {
            "description": "Not Found - If request doesn't exist",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal Server Error - If an unexpected error occurs",
            "model": ErrorResponse
        }
    }
)
async def rate_response(
    id: str,
    rating_data: RatingRequest,
    db: AsyncSession = Depends(get_db),
    organization: Dict[str, Any] = Depends(get_current_organization)
):
    """Rate a response with thumbs up/down and optional feedback."""
    try:
        # Try to find by request_id first
        result = await db.execute(
            select(RequestModel)
            .where(RequestModel.request_id == id)
        )
        request_record = result.scalar_one_or_none()
        
        # If not found, try by response_id
        if not request_record:
            result = await db.execute(
                select(RequestModel)
                .where(RequestModel.response_id == id)
            )
            request_record = result.scalar_one_or_none()
        
        if not request_record:
            raise HTTPException(
                status_code=404,
                detail=f"Request or response with ID {id} not found"
            )
        
        # Verify the request belongs to the organization
        # (through the API key relationship)
        api_key_result = await db.execute(
            select(APIKey)
            .where(APIKey.id == request_record.api_key_id)
        )
        api_key = api_key_result.scalar_one_or_none()
        
        if not api_key or str(api_key.organization_id) != organization["organization_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to rate this response"
            )
        
        # Update rating
        request_record.rating = rating_data.rating
        request_record.rating_feedback = rating_data.feedback
        request_record.rating_timestamp = datetime.utcnow()
        
        await db.commit()
        
        return RatingResponse(
            request_id=request_record.request_id,
            rating=rating_data.rating,
            feedback=rating_data.feedback,
            rated_at=request_record.rating_timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rating response: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error rating response: {str(e)}"
        )


# Health check endpoint is now defined above
