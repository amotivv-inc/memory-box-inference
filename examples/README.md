# OpenAI Inference Proxy Client Examples

This directory contains example code for interacting with the OpenAI Inference Proxy API.

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

### Integration Tips

1. **Store JWT tokens securely** - Don't commit them to version control
2. **Handle token expiration** - Implement token refresh logic
3. **Implement retry logic** - For transient network errors
4. **Monitor usage** - Track token consumption and costs
5. **Use session IDs** - Group related requests for better tracking

## Contributing

Feel free to extend the client with additional features or create examples in other languages!
