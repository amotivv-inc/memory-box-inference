# OpenAI Inference Proxy: Deployment Guide

This guide provides detailed instructions for deploying the OpenAI Inference Proxy on a remote server using Docker.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Application Deployment](#application-deployment)
4. [Initial Configuration](#initial-configuration)
5. [Testing the Deployment](#testing-the-deployment)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying the OpenAI Inference Proxy, ensure you have:

- A server with Docker and Docker Compose installed
- Git installed on the server
- An OpenAI API key
- Basic knowledge of Linux commands and Docker

## Server Setup

### 1. Update the Server

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y
```

### 2. Install Docker and Docker Compose

If Docker is not already installed:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add your user to the docker group
sudo usermod -aG docker $USER

# Apply group changes (or log out and back in)
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin -y
```

### 3. Configure Firewall

If you're using a firewall, allow traffic on port 8000:

```bash
# Allow traffic on port 8000
sudo ufw allow 8000/tcp

# Enable the firewall if not already enabled
sudo ufw enable
```

## Application Deployment

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/your-repo/openai-inference-proxy.git
cd openai-inference-proxy
```

### 2. Configure Environment Variables

Create a `.env` file based on the example:

```bash
# Copy the example environment file
cp .env.example .env

# Generate a Fernet key for encryption
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate a JWT secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Edit the `.env` file with your preferred text editor:

```bash
# Edit the .env file
nano .env
```

Update the following variables:

```
# Database Configuration
DATABASE_URL=postgresql+asyncpg://proxyuser:proxypass@postgres:5432/openai_proxy

# Security Keys
JWT_SECRET_KEY=your_generated_jwt_secret
ENCRYPTION_KEY=your_generated_fernet_key

# OpenAI Configuration
OPENAI_API_BASE_URL=https://api.openai.com/v1

# CORS Configuration
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false

# Logging
LOG_LEVEL=INFO
```

### 3. Deploy with Docker Compose

```bash
# Deploy the application
docker-compose -f docker/docker-compose.yml up -d
```

This will:
1. Start a PostgreSQL container
2. Start the API container
3. Initialize the database schema automatically

### 4. Verify Deployment

```bash
# Check if containers are running
docker ps

# Check API container logs
docker logs openai-proxy-api
```

## Initial Configuration

After deploying the application, you need to set up organizations, users, and API keys.

### 1. Create an Organization

```bash
# Connect to the API container
docker exec -it openai-proxy-api bash

# Create an organization
python scripts/manage_api_keys.py create-org "Your Organization Name"
```

Save the organization ID for the next steps.

### 2. Create a User (Optional)

```bash
# Create a user
python scripts/manage_users.py create-user <org-id> "user123"
```

### 3. Add an OpenAI API Key

You can create API keys at two levels:

#### Organization-Wide Key (Shared)
```bash
# Add an organization-wide OpenAI API key
python scripts/manage_api_keys.py create-key <org-id> <your-openai-key> --name "Production Key"
```

#### User-Specific Key (For Audit Compliance)
```bash
# First create a user (if needed)
python scripts/manage_users.py create-user <org-id> "alice@example.com"

# Then create a user-specific key
python scripts/manage_api_keys.py create-key <org-id> <your-openai-key> --user-id <user-internal-id> --name "Alice's Key"
```

Save the synthetic key for API requests. The system will automatically select the appropriate key based on the user making the request.

### 4. Generate a JWT Token

```bash
# Generate a JWT token
python scripts/create_jwt.py --org-name "Your Organization Name" --org-id <org-id>
```

Save the JWT token for authentication.

## Testing the Deployment

Use the comprehensive test script to verify that all endpoints are working:

```bash
# Run the test script (it will create its own test organization)
python tests/openai_proxy_test.py

# Or run with a custom OpenAI API key
TEST_OPENAI_KEY="sk-your-test-key" python tests/openai_proxy_test.py
```

The test script will:
- Create a test organization
- Generate JWT tokens
- Test all API endpoints
- Verify user-scoped API key functionality
- Test streaming and non-streaming responses
- Validate error handling

Alternatively, you can test individual endpoints with curl:

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

## Monitoring and Maintenance

### Monitoring Logs

```bash
# Monitor API logs in real-time
docker logs -f openai-proxy-api

# Monitor database logs
docker logs -f openai-inference-proxy-db
```

### Backing Up the Database

```bash
# Create a backup of the PostgreSQL database
docker exec -t openai-inference-proxy-db pg_dumpall -c -U proxyuser > backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

### Updating the Application

```bash
# Pull the latest changes
git pull

# Rebuild and restart the containers
docker-compose -f docker/docker-compose.yml up -d --build
```

### Scaling (Advanced)

For high-traffic deployments, consider:

1. Using a managed PostgreSQL service
2. Setting up a load balancer
3. Implementing Redis for rate limiting
4. Using a reverse proxy like Nginx

## Troubleshooting

### Common Issues

#### Database Connection Errors

If the API container can't connect to the database:

```bash
# Check if the PostgreSQL container is running
docker ps | grep openai-inference-proxy-db

# Check PostgreSQL logs
docker logs openai-inference-proxy-db

# Restart the PostgreSQL container
docker-compose -f docker/docker-compose.yml restart postgres
```

#### API Container Not Starting

If the API container fails to start:

```bash
# Check API container logs
docker logs openai-proxy-api

# Verify environment variables
docker exec -it openai-proxy-api env | grep -E 'JWT_SECRET|DATABASE_URL|ENCRYPTION_KEY'
```

#### Authentication Issues

If you're getting authentication errors:

```bash
# Generate a new JWT token
docker exec -it openai-proxy-api python scripts/create_jwt.py --org-name "Your Organization Name" --org-id <org-id>

# Verify the organization exists
docker exec -it openai-proxy-api python scripts/manage_api_keys.py list-orgs
```

#### OpenAI API Errors

If you're getting errors from the OpenAI API:

```bash
# Verify your API key is active
docker exec -it openai-proxy-api python scripts/manage_api_keys.py list-keys

# Create a new API key
docker exec -it openai-proxy-api python scripts/manage_api_keys.py create-key <org-id> <new-openai-key> --name "New Key"
```

For more detailed administration instructions, see the [Admin Guide](admin-guide.md).
