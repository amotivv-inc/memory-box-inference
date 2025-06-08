#!/usr/bin/env python3
"""
Example client for OpenAI Inference Proxy

This client demonstrates how to interact with the OpenAI Inference Proxy API,
including authentication, making requests, handling streaming responses, and
rating responses.

Note: The proxy uses user-scoped API keys. When you make a request with your
X-User-ID header, the proxy will:
1. First look for a user-specific OpenAI API key
2. Fall back to an organization-wide key if no user key exists
3. Return 403 Forbidden if no keys are available
"""

import asyncio
import httpx
import json
from typing import Optional, AsyncGenerator, Dict, Any


class OpenAIProxyClient:
    """Simple client for interacting with the OpenAI Inference Proxy"""
    
    def __init__(self, base_url: str, jwt_token: str, user_id: str):
        """
        Initialize the client.
        
        Args:
            base_url: The proxy API base URL (e.g., http://localhost:8000)
            jwt_token: JWT token for authentication (obtained via create_jwt.py)
            user_id: Your user identifier (e.g., email or username)
        """
        self.base_url = base_url.rstrip('/')
        self.jwt_token = jwt_token
        self.user_id = user_id
        self.session_id = None
        
    @property
    def headers(self) -> Dict[str, str]:
        """Common headers for all requests"""
        headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "X-User-ID": self.user_id,
            "Content-Type": "application/json"
        }
        if self.session_id:
            headers["X-Session-ID"] = self.session_id
        return headers
    
    async def create_response(
        self, 
        prompt: str, 
        model: str = "gpt-4o-mini",
        stream: bool = False,
        persona_id: Optional[str] = None,
        **kwargs
    ) -> tuple[Dict[str, Any], Optional[str], Optional[str]]:
        """
        Create a non-streaming response.
        
        Args:
            prompt: The input text to send to the model
            model: The model to use (e.g., "gpt-4o", "gpt-4o-mini")
            stream: Whether to stream the response
            persona_id: Optional ID of a persona (system prompt) to use
            **kwargs: Additional parameters to pass to the API
        
        Returns:
            Tuple of (response_data, request_id, response_id)
        """
        request_data = {
            "input": prompt,
            "model": model,
            "stream": stream,
            **kwargs
        }
        
        # Add persona_id if provided
        if persona_id:
            request_data["persona_id"] = persona_id
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/responses",
                headers=self.headers,
                json=request_data
            )
            response.raise_for_status()
            
            # Extract IDs from headers
            request_id = response.headers.get("X-Request-ID")
            if not self.session_id:
                self.session_id = response.headers.get("X-Session-ID")
            
            # Parse response
            data = response.json()
            response_id = data.get("id")  # OpenAI response ID
            
            return data, request_id, response_id
    
    async def stream_response(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        persona_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a streaming response.
        
        Args:
            prompt: The input text to send to the model
            model: The model to use (e.g., "gpt-4o", "gpt-4o-mini")
            persona_id: Optional ID of a persona (system prompt) to use
            **kwargs: Additional parameters to pass to the API
            
        Yields:
            Parsed SSE event data
        """
        request_id = None
        
        request_data = {
            "input": prompt,
            "model": model,
            "stream": True,
            **kwargs
        }
        
        # Add persona_id if provided
        if persona_id:
            request_data["persona_id"] = persona_id
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/responses",
                headers=self.headers,
                json=request_data,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                # Extract IDs from headers
                request_id = response.headers.get("X-Request-ID")
                if not self.session_id:
                    self.session_id = response.headers.get("X-Session-ID")
                
                # Store request ID for later use
                self.last_request_id = request_id
                
                # Process SSE stream
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() and data_str != "[DONE]":
                            try:
                                data = json.loads(data_str)
                                yield data
                            except json.JSONDecodeError:
                                # Skip malformed data
                                pass
    
    async def get_response(self, response_id: str) -> Dict[str, Any]:
        """Get a response by its OpenAI response ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/responses/{response_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def rate_response(
        self,
        id: str,  # Can be either request_id or response_id
        rating: int,
        feedback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rate a response.
        
        Args:
            id: Either the request ID (req_xxx) or response ID (resp_xxx)
            rating: 1 for positive, -1 for negative
            feedback: Optional feedback text
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/responses/{id}/rate",
                headers=self.headers,
                json={
                    "rating": rating,
                    "feedback": feedback
                }
            )
            response.raise_for_status()
            return response.json()
    
    # Persona Management Methods
    
    async def list_personas(self) -> Dict[str, Any]:
        """List all personas available to the user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/personas",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """Get details of a specific persona"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/personas/{persona_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_persona(
        self,
        name: str,
        content: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new persona.
        
        Args:
            name: Name of the persona
            content: System prompt content
            description: Optional description
        """
        request_data = {
            "name": name,
            "content": content
        }
        
        if description:
            request_data["description"] = description
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/personas",
                headers=self.headers,
                json=request_data
            )
            response.raise_for_status()
            return response.json()
    
    async def update_persona(
        self,
        persona_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing persona.
        
        Args:
            persona_id: ID of the persona to update
            name: New name (optional)
            content: New system prompt content (optional)
            description: New description (optional)
        """
        request_data = {}
        
        if name:
            request_data["name"] = name
        if content:
            request_data["content"] = content
        if description:
            request_data["description"] = description
            
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.base_url}/v1/personas/{persona_id}",
                headers=self.headers,
                json=request_data
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_persona(self, persona_id: str) -> Dict[str, Any]:
        """Delete a persona"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/v1/personas/{persona_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_persona_analytics(self, persona_id: str) -> Dict[str, Any]:
        """Get analytics for a specific persona"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v1/analytics/personas/{persona_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


async def main():
    """Example usage of the client"""
    
    # Configuration
    BASE_URL = "http://localhost:8000"
    JWT_TOKEN = "your-jwt-token-here"  # Get this from scripts/create_jwt.py
    USER_ID = "test-user@example.com"  # Your user identifier
    
    # Create client
    client = OpenAIProxyClient(BASE_URL, JWT_TOKEN, USER_ID)
    
    print("=== OpenAI Proxy Client Example ===\n")
    
    # Example 1: Non-streaming request
    print("1. Non-streaming request:")
    try:
        response_data, request_id, response_id = await client.create_response(
            prompt="What is the capital of France? Answer in one sentence.",
            model="gpt-4o-mini",
            temperature=0.7,
            max_output_tokens=50
        )
        
        # Extract the response text from the content array
        if response_data.get("content"):
            output_text = response_data["content"][0].get("text", "")
            print(f"Response: {output_text}")
        else:
            print("No content in response")
        
        print(f"Request ID: {request_id}")
        print(f"Response ID: {response_id}")
        
        # Show usage information
        if "usage" in response_data:
            usage = response_data["usage"]
            print(f"Tokens used: {usage.get('total_tokens', 0)}")
        
        print()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print("Error 403: No API key available for your user/organization")
            print("Make sure an API key is configured for your organization or user")
        else:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    
    # Example 2: Streaming request
    print("2. Streaming request:")
    try:
        print("Response: ", end="", flush=True)
        
        full_response = ""
        response_id = None
        
        async for event in client.stream_response(
            prompt="Count from 1 to 5 with enthusiasm!",
            model="gpt-4o-mini",
            temperature=0.9,
            max_output_tokens=100
        ):
            # Handle the streaming events
            if "content" in event and event["content"]:
                # Extract text from content array
                for content_item in event["content"]:
                    if "text" in content_item:
                        text = content_item["text"]
                        print(text, end="", flush=True)
                        full_response += text
            
            # Capture the response ID if available
            if "id" in event:
                response_id = event["id"]
        
        print("\n")
        print(f"Request ID: {getattr(client, 'last_request_id', 'N/A')}")
        print(f"Response ID: {response_id}")
        print()
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print("\nError 403: No API key available for your user/organization")
        else:
            print(f"\nHTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"\nError: {e}")
    
    print()
    
    # Example 3: Rate a response by request ID
    if request_id:
        print("3. Rating response by request ID:")
        try:
            rating_response = await client.rate_response(
                id=request_id,
                rating=1,  # Positive rating
                feedback="Great response!"
            )
            print(f"Rating submitted successfully")
            print(f"Rated at: {rating_response.get('rated_at', 'N/A')}")
            
        except Exception as e:
            print(f"Error rating: {e}")
    
    print()
    
    # Example 4: Rate a response by response ID
    if response_id:
        print("4. Rating response by response ID:")
        try:
            rating_response = await client.rate_response(
                id=response_id,
                rating=-1,  # Negative rating
                feedback="Could be more detailed"
            )
            print(f"Rating submitted successfully")
            print(f"Rated at: {rating_response.get('rated_at', 'N/A')}")
            
        except Exception as e:
            print(f"Error rating: {e}")
    
    print()
    
    # Example 5: Get response by ID (if using real OpenAI key)
    if response_id and not response_id.startswith("test-"):
        print("5. Retrieving response by ID:")
        try:
            retrieved = await client.get_response(response_id)
            print(f"Retrieved response ID: {retrieved.get('id', 'N/A')}")
            print(f"Model used: {retrieved.get('model', 'N/A')}")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                print("Response not found (this is normal with test API keys)")
            else:
                print(f"Error: {e.response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
    
    print()
    
    # Example 6: Using a persona (uncomment to test with a real persona ID)
    """
    print("6. Using a persona:")
    try:
        # Replace with a real persona ID from your system
        persona_id = "7f9a815f-576b-f770-777e-cff14a1099e7"
        
        response_data, request_id, response_id = await client.create_response(
            prompt="How can I optimize my website's performance?",
            model="gpt-4o-mini",
            persona_id=persona_id,
            temperature=0.7,
            max_output_tokens=150
        )
        
        # Extract the response text from the content array
        if response_data.get("content"):
            output_text = response_data["content"][0].get("text", "")
            print(f"Response: {output_text}")
        else:
            print("No content in response")
        
        print(f"Request ID: {request_id}")
        print(f"Response ID: {response_id}")
        print(f"Using persona ID: {persona_id}")
        
        # Show usage information
        if "usage" in response_data:
            usage = response_data["usage"]
            print(f"Tokens used: {usage.get('total_tokens', 0)}")
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    """
    print(f"Session ID: {client.session_id}")
    print("\n=== Example Complete ===")
    
    # Example 7: Persona management (uncomment to test)
    """
    print("7. Persona Management:")
    
    # 7.1 Create a new persona
    try:
        print("\n7.1 Creating a new persona:")
        new_persona = await client.create_persona(
            name="Technical Writer",
            content="You are a technical writer who specializes in creating clear, concise documentation for software products. Use simple language, avoid jargon when possible, and structure your responses with headings and bullet points for readability.",
            description="For creating technical documentation"
        )
        print(f"Persona created: {new_persona.get('name')} ({new_persona.get('id')})")
        
        # Save the persona ID for later use
        created_persona_id = new_persona.get('id')
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 7.2 List all personas
    try:
        print("\n7.2 Listing all personas:")
        personas = await client.list_personas()
        
        if "items" in personas and personas["items"]:
            for persona in personas["items"]:
                print(f"- {persona.get('name')} ({persona.get('id')})")
                print(f"  Description: {persona.get('description', 'N/A')}")
                print(f"  Content Length: {len(persona.get('content', ''))} characters")
                print(f"  User Restricted: {'Yes' if persona.get('user_id') else 'No (Organization-wide)'}")
                print()
        else:
            print("No personas found")
        
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 7.3 Use the newly created persona
    if 'created_persona_id' in locals():
        try:
            print("\n7.3 Using the newly created persona:")
            response_data, request_id, response_id = await client.create_response(
                prompt="Write a brief introduction for a REST API documentation.",
                model="gpt-4o-mini",
                persona_id=created_persona_id,
                temperature=0.7,
                max_output_tokens=200
            )
            
            # Extract the response text from the content array
            if response_data.get("content"):
                output_text = response_data["content"][0].get("text", "")
                print(f"Response: {output_text}")
            else:
                print("No content in response")
            
            print(f"Request ID: {request_id}")
            print(f"Response ID: {response_id}")
            print(f"Using persona ID: {created_persona_id}")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # 7.4 Get persona analytics
    if 'created_persona_id' in locals():
        try:
            print("\n7.4 Getting persona analytics:")
            analytics = await client.get_persona_analytics(created_persona_id)
            
            print(f"Persona: {analytics.get('name')} ({analytics.get('id')})")
            print(f"Total Requests: {analytics.get('request_count', 0)}")
            print(f"Success Rate: {analytics.get('success_rate', 0)}%")
            print(f"Total Tokens: {analytics.get('total_tokens', 0)}")
            print(f"Total Cost: ${analytics.get('total_cost', 0):.2f}")
            
            # Print daily usage if available
            if "daily_usage" in analytics and analytics["daily_usage"]:
                print("\nDaily Usage:")
                for day in analytics["daily_usage"]:
                    print(f"- {day.get('date')}: {day.get('request_count')} requests, {day.get('total_tokens')} tokens, ${day.get('total_cost', 0):.2f}")
            
            # Print model usage if available
            if "model_usage" in analytics and analytics["model_usage"]:
                print("\nModel Usage:")
                for model in analytics["model_usage"]:
                    print(f"- {model.get('model')}: {model.get('request_count')} requests")
            
            # Print top users if available
            if "top_users" in analytics and analytics["top_users"]:
                print("\nTop Users:")
                for user in analytics["top_users"]:
                    print(f"- {user.get('external_user_id')}: {user.get('request_count')} requests, {user.get('total_tokens')} tokens")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # 7.5 Update the persona
    if 'created_persona_id' in locals():
        try:
            print("\n7.5 Updating the persona:")
            updated_persona = await client.update_persona(
                persona_id=created_persona_id,
                name="Advanced Technical Writer",
                content="You are an advanced technical writer with expertise in API documentation. Create clear, structured documentation with examples, parameter descriptions, and response formats. Use markdown formatting for headings, code blocks, and tables.",
                description="For creating advanced API documentation"
            )
            print(f"Persona updated: {updated_persona.get('name')} ({updated_persona.get('id')})")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")
    
    # 7.6 Delete the persona
    if 'created_persona_id' in locals():
        try:
            print("\n7.6 Deleting the persona:")
            result = await client.delete_persona(created_persona_id)
            print(f"Persona deleted: {result.get('message', 'Success')}")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            print(f"Error: {e}")
    """
    
    # Additional notes
    print("\nNotes:")
    print("- The proxy automatically selects the appropriate OpenAI API key based on your user")
    print("- User-specific keys take precedence over organization-wide keys")
    print("- All requests are logged with full audit trail")
    print("- Use 'docker exec openai-proxy-api python scripts/create_jwt.py' to generate JWT tokens")
    print("- Personas can be used to customize AI behavior for different use cases")
    print("- Persona analytics help optimize system prompts based on usage patterns")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
