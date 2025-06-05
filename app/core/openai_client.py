"""OpenAI API client wrapper for proxying requests"""

import httpx
import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from app.config import settings
from app.models.requests import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Async client for OpenAI API with streaming support"""
    
    def __init__(self):
        self.base_url = settings.openai_api_base_url
        self.timeout = httpx.Timeout(settings.openai_timeout)
        
    async def create_response(
        self,
        api_key: str,
        request_data: Dict[str, Any],
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Create a response using OpenAI's Responses API
        
        Args:
            api_key: OpenAI API key
            request_data: Request payload
            stream: Whether to stream the response
            
        Yields:
            Response chunks (for streaming) or complete response
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Force stream parameter based on our stream flag
        request_data["stream"] = stream
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if stream:
                    # Streaming request
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/responses",
                        headers=headers,
                        json=request_data
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            yield self._format_error_response(
                                response.status_code,
                                error_text.decode()
                            )
                            return
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                yield line + "\n\n"
                else:
                    # Non-streaming request
                    response = await client.post(
                        f"{self.base_url}/responses",
                        headers=headers,
                        json=request_data
                    )
                    
                    if response.status_code != 200:
                        yield self._format_error_response(
                            response.status_code,
                            response.text
                        )
                        return
                    
                    yield response.text
                    
            except httpx.TimeoutException:
                logger.error("OpenAI API request timed out")
                yield self._format_error_response(
                    504,
                    "OpenAI API request timed out"
                )
            except httpx.RequestError as e:
                logger.error(f"OpenAI API request error: {e}")
                yield self._format_error_response(
                    502,
                    f"Error connecting to OpenAI API: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Unexpected error in OpenAI client: {e}")
                yield self._format_error_response(
                    500,
                    f"Internal server error: {str(e)}"
                )
    
    def _format_error_response(self, status_code: int, error_text: str) -> str:
        """Format error response to match OpenAI's error format"""
        try:
            # Try to parse as JSON first
            error_data = json.loads(error_text)
            return json.dumps(error_data)
        except:
            # Create our own error format
            error_response = ErrorResponse(
                error=ErrorDetail(
                    type="proxy_error",
                    message=error_text,
                    code=f"HTTP_{status_code}"
                )
            )
            return error_response.model_dump_json()
    
    async def get_response(self, api_key: str, response_id: str) -> Dict[str, Any]:
        """
        Get a specific response by ID
        
        Args:
            api_key: OpenAI API key
            response_id: Response ID to retrieve
            
        Returns:
            Response data
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/responses/{response_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"OpenAI API error: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                
                return response.json()
                
            except httpx.RequestError as e:
                logger.error(f"Error getting response from OpenAI: {e}")
                raise
    
    async def cancel_response(self, api_key: str, response_id: str) -> Dict[str, Any]:
        """
        Cancel a response
        
        Args:
            api_key: OpenAI API key
            response_id: Response ID to cancel
            
        Returns:
            Cancelled response data
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/responses/{response_id}/cancel",
                    headers=headers
                )
                
                if response.status_code != 200:
                    raise httpx.HTTPStatusError(
                        f"OpenAI API error: {response.status_code}",
                        request=response.request,
                        response=response
                    )
                
                return response.json()
                
            except httpx.RequestError as e:
                logger.error(f"Error cancelling response: {e}")
                raise


# Global client instance
openai_client = OpenAIClient()
