"""Utilities for handling streaming responses"""

import json
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """Server-Sent Event data structure"""
    event: Optional[str] = None
    data: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None


def parse_sse_event(line: str) -> Optional[SSEEvent]:
    """
    Parse a single SSE line into an event object
    
    Args:
        line: SSE line to parse
        
    Returns:
        SSEEvent object or None if invalid
    """
    if not line or not line.strip():
        return None
    
    if line.startswith("event: "):
        return SSEEvent(event=line[7:].strip())
    elif line.startswith("data: "):
        return SSEEvent(data=line[6:].strip())
    elif line.startswith("id: "):
        return SSEEvent(id=line[4:].strip())
    elif line.startswith("retry: "):
        try:
            retry_value = int(line[7:].strip())
            return SSEEvent(retry=retry_value)
        except ValueError:
            return None
    
    return None


class StreamingResponseHandler:
    """Handler for processing streaming responses from OpenAI"""
    
    def __init__(self):
        self.usage_data = None
        self.response_data = None
        self.error_data = None
        self.response_id = None  # Added to store OpenAI's response ID
        
    async def process_stream(
        self, 
        stream: AsyncGenerator[str, None],
        request_id: str,
        session_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Process streaming response and extract usage data
        
        Args:
            stream: Async generator of response chunks
            request_id: Request ID for tracking
            session_id: Session ID for tracking
            
        Yields:
            Modified response chunks with added headers
        """
        try:
            async for chunk in stream:
                # Check if it's an error response - only consider it an error if the error field exists AND is not null
                if chunk.startswith("{"):
                    try:
                        data = json.loads(chunk)
                        if "error" in data and data["error"] is not None:
                            self.error_data = data
                            yield chunk
                            continue
                    except json.JSONDecodeError:
                        # Not valid JSON, continue with normal processing
                        pass
                
                # Process SSE events
                if chunk.startswith("data: "):
                    try:
                        # Extract the JSON data
                        data_str = chunk[6:].strip()
                        if data_str and data_str != "[DONE]":
                            data = json.loads(data_str)
                            
                            # Check for response completion event
                            if data.get("type") == "response.completed":
                                response = data.get("response", {})
                                self.usage_data = response.get("usage")
                                self.response_data = response
                                self.response_id = response.get("id")  # Extract response ID
                                logger.info(f"Captured usage data for request {request_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse SSE data: {e}")
                
                # Forward the chunk with custom headers
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in streaming handler: {e}")
            error_response = {
                "error": {
                    "type": "streaming_error",
                    "message": str(e),
                    "code": "STREAM_ERROR"
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    def format_sse_message(self, event: str, data: Dict[str, Any]) -> str:
        """
        Format a message as SSE
        
        Args:
            event: Event name
            data: Data to send
            
        Returns:
            Formatted SSE string
        """
        lines = []
        if event:
            lines.append(f"event: {event}")
        lines.append(f"data: {json.dumps(data)}")
        return "\n".join(lines) + "\n\n"
    
    def inject_metadata(self, request_id: str, session_id: str) -> str:
        """
        Create metadata event to inject into stream
        
        Args:
            request_id: Request ID
            session_id: Session ID
            
        Returns:
            SSE formatted metadata event
        """
        metadata = {
            "request_id": request_id,
            "session_id": session_id
        }
        return self.format_sse_message("metadata", metadata)
