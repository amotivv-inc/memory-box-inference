# API Tests

This directory contains comprehensive tests for the OpenAI Inference Proxy API.

## Test Files

- `openai_proxy_test.py`: Comprehensive Python script that tests all API endpoints and functionality

## Running Tests

To run the tests, make sure the API is running with Docker:

```bash
# Start the API (if not already running)
docker-compose -f docker/docker-compose.yml up -d

# Run the comprehensive test suite
python tests/openai_proxy_test.py
```

You can also set a custom OpenAI API key for testing:

```bash
TEST_OPENAI_KEY="sk-your-test-key" python tests/openai_proxy_test.py
```

## Test Coverage

The test suite covers:

### 1. Authentication Tests
- Unauthenticated access (should fail for protected endpoints)
- JWT token validation
- Invalid token handling

### 2. User Management
- Manual user creation
- Automatic user creation on first request
- User listing

### 3. API Key Management
- Organization-wide API key creation
- User-specific API key creation
- API key listing
- Key activation/deactivation

### 4. Response Endpoints
- Non-streaming responses
- Streaming responses (SSE)
- Response retrieval by ID
- Response rating (by request_id and response_id)

### 5. User-Scoped API Key Validation
- User with specific key can access API
- User without key is denied when no org-wide key exists
- Fallback to org-wide key when user has no specific key

### 6. Error Scenarios
- Invalid JWT tokens
- Missing required headers (X-User-ID)
- Invalid model names
- Non-existent resources

### 7. Health Checks
- Unauthenticated health check
- Authenticated health check with OpenAI connectivity test

## Test Output

The test script provides colored output for easy reading:

```
OpenAI Inference Proxy - Comprehensive Test Suite
================================================

=== Checking API Health ===
✓ API is healthy

=== Creating Test Organization ===
✓ Created organization: Test Organization 1735251925 (ID: 123e4567-e89b-12d3-a456-426614174000)

=== Test 1: Unauthenticated Access ===
✓ Health endpoint accessible without auth
✓ Protected endpoint correctly requires auth

... (more tests)

Test suite completed!
```

## Test Data

The test script:
- Creates a new test organization with a unique name
- Generates test users and API keys
- Uses test data that won't interfere with production

**Note**: Test data is not automatically cleaned up. The script will display the test organization ID at the end for manual cleanup if needed.

## Prerequisites

- Docker and Docker Compose installed
- API running on http://localhost:8000
- `jq` installed for JSON parsing (usually pre-installed on most systems)
- `curl` for making HTTP requests

## Troubleshooting

If tests fail:

1. **Check API is running**: 
   ```bash
   docker ps | grep openai-proxy-api
   ```

2. **Check API logs**:
   ```bash
   docker logs openai-proxy-api
   ```

3. **Verify database is running**:
   ```bash
   docker ps | grep openai-proxy-db
   ```

4. **Check if using real OpenAI API key**:
   - Tests will show HTTP 400 errors with test keys
   - This is expected behavior
   - The important thing is that the proxy itself works

## Adding New Tests

To add new tests to the suite:

1. Add a new test function following the naming pattern `test_feature_name()`
2. Use the helper functions for consistent output:
   - `print_header()` - For test section headers
   - `print_success()` - For successful test results
   - `print_error()` - For failed test results
   - `print_info()` - For informational messages
3. Add the function call to the `main()` function
4. Ensure proper error handling and clear output

## CI/CD Integration

This test script can be integrated into CI/CD pipelines:

```bash
# Exit code 0 on success, non-zero on failure
python tests/openai_proxy_test.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Tests failed!"
    exit 1
fi
