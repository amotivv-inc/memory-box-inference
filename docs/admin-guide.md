# OpenAI Inference Proxy: Administration Guide

This comprehensive guide covers all aspects of managing organizations and API keys in the OpenAI Inference Proxy, including Docker commands for connecting to the API container and detailed instructions for all administrative tasks.

## Table of Contents

1. [Initial Deployment](#initial-deployment)
2. [Connecting to the API Container](#connecting-to-the-api-container)
3. [Managing Organizations](#managing-organizations)
4. [Managing API Keys](#managing-api-keys)
5. [Managing Users](#managing-users)
6. [Generating JWT Tokens](#generating-jwt-tokens)
7. [Testing the API](#testing-the-api)
8. [Troubleshooting](#troubleshooting)

## Initial Deployment

To deploy the OpenAI Inference Proxy on a remote Docker server:

```bash
# Clone the repository
git clone https://github.com/your-repo/openai-inference-proxy.git
cd openai-inference-proxy

# Deploy with Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

The database will be automatically initialized when the containers start for the first time. The initialization process is handled by the FastAPI application's `lifespan` context manager in `app/main.py`, which calls the `init_db()` function in `app/core/database.py`.

## Connecting to the API Container

To run management commands, you need to connect to the API container:

```bash
# Connect to the API container
docker exec -it openai-proxy-api bash

# Once inside the container, you can run management scripts
# All examples below assume you're already connected to the container
```

## Managing Organizations

Organizations are the top-level entities in the system. Each organization can have multiple API keys and users.

### Creating an Organization

```bash
# Create a new organization
python scripts/manage_api_keys.py create-org "Your Organization Name"

# Example output:
# Organization created successfully!
# ID: bc88026d-14ec-447c-abf5-c4bb582c5703
# Name: Your Organization Name
```

Save the organization ID for future use.

### Listing Organizations

```bash
# List all organizations
python scripts/manage_api_keys.py list-orgs

# Example output:
# Organizations:
# ------------------------------------------------------------
# ID: bc88026d-14ec-447c-abf5-c4bb582c5703
# Name: Your Organization Name
# Created: 2025-06-05 12:00:00.123456
# ------------------------------------------------------------
```

## Managing API Keys

API keys map organizations to OpenAI API keys. Each organization can have multiple API keys.

### Creating an API Key

API keys can be created at two levels:

#### Organization-Wide API Key
Accessible by any user in the organization:

```bash
# Create a new API key for an organization
python scripts/manage_api_keys.py create-key <org-id> <your-openai-key>

# Example with optional parameters:
python scripts/manage_api_keys.py create-key bc88026d-14ec-447c-abf5-c4bb582c5703 sk-abcdef123456 --name "Production Key" --description "For production use only"

# Example output:
# API key created successfully!
# Organization: Your Organization Name
# Name: Production Key
# Synthetic Key: sk-proxy-abc123def456
#
# Use this synthetic key in your API requests.
```

#### User-Specific API Key
Restricted to a specific user for audit compliance:

```bash
# Create a user-specific API key
python scripts/manage_api_keys.py create-key <org-id> <your-openai-key> --user-id <user-internal-id> --name "User's Personal Key"

# Example:
python scripts/manage_api_keys.py create-key bc88026d-14ec-447c-abf5-c4bb582c5703 sk-userkey123456 --user-id 5e6208ba-c511-46fd-b51b-6993a73b2943 --name "Alice's Key"
```

The synthetic key is what your clients will use to authenticate with the proxy. The actual OpenAI API key is encrypted and stored securely.

**Key Resolution Priority**:
1. User-specific key (if exists and active)
2. Organization-wide key (fallback)
3. 403 Forbidden (if no keys available)

### Listing API Keys

```bash
# List all API keys
python scripts/manage_api_keys.py list-keys

# List API keys for a specific organization
python scripts/manage_api_keys.py list-keys --org-id bc88026d-14ec-447c-abf5-c4bb582c5703

# Example output:
# API Keys:
# --------------------------------------------------------------------------------
# ID: 7e9a815f-576b-f770-777e-cff14a1099e6
# Organization: Your Organization Name (bc88026d-14ec-447c-abf5-c4bb582c5703)
# User: None
# Name: Production Key
# Description: For production use only
# Synthetic Key: sk-proxy-abc123def456
# Active: True
# Created: 2025-06-05 12:05:00.123456
# --------------------------------------------------------------------------------
```

### Deactivating an API Key

```bash
# Deactivate an API key
python scripts/manage_api_keys.py deactivate-key sk-proxy-abc123def456

# Example output:
# API key deactivated: sk-proxy-abc123def456
```

## Managing Users

Users belong to organizations and can have API keys associated with them.

### Creating a User

```bash
# Create a new user in an organization
python scripts/manage_users.py create-user <org-id> <user-id>

# Example:
python scripts/manage_users.py create-user bc88026d-14ec-447c-abf5-c4bb582c5703 user123

# Example output:
# User created successfully!
# Organization: Your Organization Name
# User ID: user123
# Internal ID: 5e6208ba-c511-46fd-b51b-6993a73b2943
```

The user ID can be any string that identifies the user in your system.

### Listing Users

```bash
# List all users
python scripts/manage_users.py list-users

# List users for a specific organization
python scripts/manage_users.py list-users --org-id bc88026d-14ec-447c-abf5-c4bb582c5703

# Example output:
# Users for Organization: Your Organization Name (bc88026d-14ec-447c-abf5-c4bb582c5703)
# --------------------------------------------------------------------------------
# ID: 5e6208ba-c511-46fd-b51b-6993a73b2943
# User ID: user123
# Created: 2025-06-05 12:10:00.123456
# --------------------------------------------------------------------------------
```

### Deleting a User

```bash
# Delete a user
python scripts/manage_users.py delete-user 5e6208ba-c511-46fd-b51b-6993a73b2943

# Example output:
# User deleted successfully!
# Organization: Your Organization Name
# User ID: user123
```

## Generating JWT Tokens

JWT tokens are used for authentication. Each token is associated with an organization.

```bash
# Generate a JWT token for an organization
python scripts/create_jwt.py --org-name "Your Organization Name" --org-id bc88026d-14ec-447c-abf5-c4bb582c5703

# Example output:
# ============================================================
# JWT TOKEN CREATED SUCCESSFULLY
# ============================================================
# Organization ID: bc88026d-14ec-447c-abf5-c4bb582c5703
# Organization Name: Your Organization Name
# Expires: 2026-06-05T12:15:00.123456Z
# Valid for: 365 days
#
# Token:
# ------------------------------------------------------------
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiYzg4MDI2ZC0xNGVjLTQ0N2MtYWJmNS1jNGJiNTgyYzU3MDMiLCJvcmdfbmFtZSI6IlRlc3QgT3JnYW5pemF0aW9uIiwiaWF0IjoxNzQ5MTM3MjMwLCJleHAiOjE3ODA2NzMyMzB9.9gV1sewZFq4o1rH4EdQRupDsuS4cn6tEUJnsl6Ep_QY
# ------------------------------------------------------------
#
# Use this token in the Authorization header:
# Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiYzg4MDI2ZC0xNGVjLTQ0N2MtYWJmNS1jNGJiNTgyYzU3MDMiLCJvcmdfbmFtZSI6IlRlc3QgT3JnYW5pemF0aW9uIiwiaWF0IjoxNzQ5MTM3MjMwLCJleHAiOjE3ODA2NzMyMzB9.9gV1sewZFq4o1rH4EdQRupDsuS4cn6tEUJnsl6Ep_QY
# ============================================================
```

You can also generate a token with a custom expiration:

```bash
# Generate a token valid for 30 days
python scripts/create_jwt.py --org-name "Your Organization Name" --org-id bc88026d-14ec-447c-abf5-c4bb582c5703 --days 30
```

## Testing the API

After setting up organizations, API keys, and JWT tokens, you can test the API:

### Quick Testing
```bash
# Test the health endpoint
curl -X GET "http://your-server:8000/v1/responses/health" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-User-ID: user123"

# Test the responses endpoint
curl -X POST "http://your-server:8000/v1/responses" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "X-User-ID: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "input": "What is the capital of France?",
    "temperature": 0.7,
    "max_output_tokens": 100
  }'
```

### Comprehensive Testing
Run the full test suite to verify all endpoints:

```bash
# Exit the container first (if you're inside)
exit

# Run the comprehensive test script
python tests/openai_proxy_test.py
```

This will test:
- Authentication and authorization
- User management (manual and auto-creation)
- API key management (org-wide and user-scoped)
- Response endpoints (streaming and non-streaming)
- Response rating functionality
- Error handling

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:

```bash
# Check if the PostgreSQL container is running
docker ps | grep openai-inference-proxy-db

# Check PostgreSQL logs
docker logs openai-inference-proxy-db

# Connect to the PostgreSQL container
docker exec -it openai-inference-proxy-db psql -U proxyuser -d openai_proxy
```

### API Container Issues

If the API container is not starting or responding:

```bash
# Check API container logs
docker logs openai-proxy-api

# Restart the API container
docker-compose -f docker/docker-compose.yml restart api

# Rebuild and restart the API container
docker-compose -f docker/docker-compose.yml up -d --build api
```

### JWT Token Issues

If you're having issues with JWT tokens:

```bash
# Generate a new JWT token
python scripts/create_jwt.py --org-name "Your Organization Name" --org-id bc88026d-14ec-447c-abf5-c4bb582c5703

# Verify the JWT token format
# The token should be in the format: header.payload.signature
# Example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Schema Updates

If you need to update the database schema:

```bash
# Connect to the PostgreSQL container
docker exec -it openai-inference-proxy-db bash

# Run psql
psql -U proxyuser -d openai_proxy

# Inside psql, run your schema updates
# For example:
\i /path/to/update_schema.sql

# Or run SQL commands directly:
ALTER TABLE api_keys ADD COLUMN new_column VARCHAR(255);
```

Alternatively, you can use the API container to run SQL scripts:

```bash
# Copy your SQL script to the API container
docker cp update_schema.sql openai-proxy-api:/tmp/

# Connect to the API container
docker exec -it openai-proxy-api bash

# Run the SQL script using psql
psql -h postgres -U proxyuser -d openai_proxy -f /tmp/update_schema.sql
