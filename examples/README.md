# OpenAI Inference Proxy Client Examples

This directory contains example code for interacting with the OpenAI Inference Proxy API.

## Analysis Client Example

The `analysis_client.py` file demonstrates how to use the conversation analysis feature:

### Features Demonstrated

1. **Creating Analysis Configurations** - Defining reusable analysis configurations
2. **Intent Classification** - Analyzing conversations for user intent
3. **Sentiment Analysis** - Determining the emotional tone of messages
4. **Urgency Detection** - Assessing the urgency level of requests
5. **Caching** - Using the caching feature for improved performance
6. **Multiple Analysis Types** - Performing different types of analysis on the same conversation

### Running the Example

```bash
# Set environment variables (optional)
export PROXY_BASE_URL="http://localhost:8000"
export PROXY_JWT_TOKEN="your-jwt-token-here"
export SAMPLE_REQUEST_ID="req_abc123"
export SAMPLE_RESPONSE_ID="resp_xyz789"

# Run the example
python examples/analysis_client.py
```

### Example Output

```
🚀 OpenAI Inference Proxy - Analysis Feature Demo
📍 Server: http://localhost:8000

1️⃣ Creating Intent Classification Configuration...
✅ Created config: Customer Support Intent Classifier (ID: 550e8400-e29b-41d4-a716-446655440000)

2️⃣ Analyzing conversation with saved config...
Intent Analysis Results
📊 Analysis Type: intent
🎯 Primary Category: technical_support
💯 Confidence: 92.00%
💭 Reasoning: The user is experiencing technical issues with the application

📈 All Categories:
   technical_support    ████████████████     92.00%
   └─ User mentions app crashes and error messages
   billing_inquiry     █                    5.00%
   feature_request                          2.00%
   account_management                       1.00%
   general_inquiry                          0.00%

📋 Metadata: {
  "sentiment": "frustrated",
  "urgency": "high",
  "topics": ["error_handling", "app_stability"]
}

💰 Cost: $0.000048
🔄 Cached: No
🤖 Model: gpt-4o-mini

3️⃣ Running same analysis again (should be cached)...
✅ Result was cached: True

4️⃣ Analyzing sentiment with inline configuration...
[Sentiment analysis results shown here]

5️⃣ Analyzing urgency using response ID...
[Urgency analysis results shown here]

✅ All analyses completed successfully!
```

### Integration Tips

1. **Create reusable configurations** for common analysis needs
2. **Analyze selectively** to optimize performance and costs
3. **Use different analysis types** for comprehensive insights
4. **Leverage caching** for frequently performed analyses
5. **Store analysis results** in your application database for historical tracking

## Python Client Example

The `client.py` file demonstrates a complete Python client implementation with all major features:

### Features Demonstrated

1. **Authentication** - Using JWT tokens with the API
2. **Non-streaming Requests** - Simple request/response pattern
3. **Streaming Requests** - Server-Sent Events (SSE) streaming
4. **Response Rating** - Rating responses by both request ID and response ID
5. **Error Handling** - Handling 403 (no API key) and other errors
6. **Session Management** - Automatic session ID tracking
7. **User-Scoped API Keys** - Understanding how the proxy selects API keys
8. **Persona Usage** - Using personas (system prompts) in requests

### Prerequisites

Install the required Python package:

```bash
pip install httpx
```

### Setup

1. **Create an Organization and Get JWT Token**:
   ```bash
   # Create organization
   docker exec openai-proxy-api python scripts/manage_api_keys.py create-org "My Organization"
   
   # Generate JWT token
   docker exec openai-proxy-api python scripts/create_jwt.py --org-name "My Organization" --org-id <org-id>
   ```

2. **Add an API Key** (organization-wide or user-specific):
   ```bash
   # Organization-wide key
   docker exec openai-proxy-api python scripts/manage_api_keys.py create-key <org-id> <openai-key>
   
   # User-specific key
   docker exec openai-proxy-api python scripts/manage_users.py create-user <org-id> "user@example.com"
   docker exec openai-proxy-api python scripts/manage_api_keys.py create-key <org-id> <openai-key> --user-id <user-internal-id>
   ```

3. **Update the Client Configuration**:
   Edit `client.py` and update these values:
   ```python
   JWT_TOKEN = "your-jwt-token-here"  # From step 1
   USER_ID = "user@example.com"       # Your user identifier
   ```

### Running the Example

```bash
python examples/client.py
```

### Example Output

```
=== OpenAI Proxy Client Example ===

1. Non-streaming request:
Response: The capital of France is Paris.
Request ID: req_abc123def456
Response ID: resp_xyz789
Tokens used: 42

2. Streaming request:
Response: 1! 2! 3! 4! 5! Woohoo!
Request ID: req_def456ghi789
Response ID: resp_uvw456

3. Rating response by request ID:
Rating submitted successfully
Rated at: 2025-06-05T18:30:00.000Z

4. Rating response by response ID:
Rating submitted successfully
Rated at: 2025-06-05T18:30:01.000Z

Session ID: session_123abc

=== Example Complete ===
```

### Understanding User-Scoped API Keys

The proxy implements a priority-based API key selection:

1. **User-Specific Keys**: If the user (identified by X-User-ID header) has a personal API key, it will be used
2. **Organization-Wide Keys**: If no user-specific key exists, the organization's shared key is used
3. **No Keys Available**: Returns 403 Forbidden

This allows for:
- **Audit Compliance**: Track exactly which user made which requests
- **Fine-grained Control**: Different users can have different OpenAI API keys
- **Flexible Access**: Users without personal keys can still use shared organization keys

### Error Handling

The client handles common error scenarios:

- **403 Forbidden**: No API key available for the user/organization
- **401 Unauthorized**: Invalid or expired JWT token
- **422 Unprocessable Entity**: Missing required headers (e.g., X-User-ID)
- **400 Bad Request**: Invalid request data or OpenAI API errors

### Advanced Usage

You can extend the client with additional features:

```python
# Custom session ID
client.session_id = "my-custom-session-123"

# Different models
response = await client.create_response(
    prompt="Hello",
    model="gpt-4o",  # or "o1-mini", "gpt-3.5-turbo", etc.
    temperature=0.5,
    max_output_tokens=1000,
    top_p=0.9
)

# Retrieve a specific response
response_data = await client.get_response("resp_abc123")
```

### Using Personas

The client can be extended to use personas (system prompts) in requests:

```python
# Using a persona in a request
response_data, request_id, response_id = await client.create_response(
    prompt="How can I optimize my website's performance?",
    model="gpt-4o",
    persona_id="7f9a815f-576b-f770-777e-cff14a1099e7"  # Technical Support persona
)

# Creating a new persona
async def create_persona(client, name, content, description=None):
    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            f"{client.base_url}/v1/personas",
            headers=client.headers,
            json={
                "name": name,
                "content": content,
                "description": description
            }
        )
        response.raise_for_status()
        return response.json()

# Listing available personas
async def list_personas(client):
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f"{client.base_url}/v1/personas",
            headers=client.headers
        )
        response.raise_for_status()
        return response.json()

# Getting persona analytics
async def get_persona_analytics(client, persona_id):
    async with httpx.AsyncClient() as http_client:
        response = await http_client.get(
            f"{client.base_url}/v1/analytics/personas/{persona_id}",
            headers=client.headers
        )
        response.raise_for_status()
        return response.json()
```

### Integration Tips

1. **Store JWT tokens securely** - Don't commit them to version control
2. **Handle token expiration** - Implement token refresh logic
3. **Implement retry logic** - For transient network errors
4. **Monitor usage** - Track token consumption and costs
5. **Use session IDs** - Group related requests for better tracking
6. **Leverage personas** - Create specialized personas for different use cases
7. **Monitor persona performance** - Use analytics to optimize your personas

## Contributing

Feel free to extend the client with additional features or create examples in other languages!
