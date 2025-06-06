#!/bin/bash

# OpenAI Inference Proxy - Quick Start Script
# This script sets up the environment and walks you through initial configuration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "OpenAI Inference Proxy - Quick Start"
echo "======================================"
echo -e "${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Determine docker compose command (with or without hyphen)
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo -e "${RED}Error: Neither docker-compose nor docker compose is available. Please install Docker Compose.${NC}"
    exit 1
fi

echo -e "${GREEN}Using Docker Compose command: ${DOCKER_COMPOSE}${NC}"

# Step 1: Set up .env file
echo -e "${YELLOW}Step 1: Setting up environment${NC}"
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Update DATABASE_URL to use Docker container
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|postgresql+asyncpg://user:password@localhost:5432/openai_proxy|postgresql+asyncpg://proxyuser:proxypass@postgres:5432/openai_proxy|" .env
else
    # Linux
    sed -i "s|postgresql+asyncpg://user:password@localhost:5432/openai_proxy|postgresql+asyncpg://proxyuser:proxypass@postgres:5432/openai_proxy|" .env
fi
echo -e "${GREEN}✓ Updated database URL${NC}"

# Update CORS_ORIGINS to use JSON format
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' 's|CORS_ORIGINS=http://localhost:3000,http://localhost:8080|CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]|' .env
else
    # Linux
    sed -i 's|CORS_ORIGINS=http://localhost:3000,http://localhost:8080|CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]|' .env
fi
echo -e "${GREEN}✓ Updated CORS format${NC}"

# Step 2: Generate Fernet key if needed
if grep -q "generate-fernet-key-for-production" .env; then
    echo
    echo "Generating Fernet encryption key..."
    FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    
    # Update .env file based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/generate-fernet-key-for-production/$FERNET_KEY/" .env
    else
        # Linux
        sed -i "s/generate-fernet-key-for-production/$FERNET_KEY/" .env
    fi
    echo -e "${GREEN}✓ Generated and saved Fernet key${NC}"
fi

# Step 3: Generate JWT secret if needed
if grep -q "your-secret-key-here-change-in-production" .env; then
    echo "Generating JWT secret key..."
    JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Update .env file based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here-change-in-production/$JWT_SECRET/" .env
    else
        # Linux
        sed -i "s/your-secret-key-here-change-in-production/$JWT_SECRET/" .env
    fi
    echo -e "${GREEN}✓ Generated and saved JWT secret${NC}"
fi

# Step 4: Start Docker containers
echo
echo -e "${YELLOW}Step 2: Starting Docker containers${NC}"
echo "Starting PostgreSQL and API containers..."
$DOCKER_COMPOSE -f docker/docker-compose.yml up -d

# Wait for API to be ready
echo
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ API is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: API failed to start. Check logs with: docker logs openai-proxy-api${NC}"
        exit 1
    fi
    echo -n "."
    sleep 1
done
echo

# Step 5: Create organization
echo
echo -e "${YELLOW}Step 3: Creating your organization${NC}"
read -p "Enter your organization name: " ORG_NAME

echo "Creating organization..."
ORG_OUTPUT=$(docker exec openai-proxy-api python scripts/manage_api_keys.py create-org "$ORG_NAME" 2>&1)
ORG_ID=$(echo "$ORG_OUTPUT" | grep "ID:" | head -1 | awk '{print $2}')

if [ -n "$ORG_ID" ]; then
    echo -e "${GREEN}✓ Organization created successfully!${NC}"
    echo -e "Organization ID: ${BLUE}$ORG_ID${NC}"
else
    echo -e "${RED}Error creating organization:${NC}"
    echo "$ORG_OUTPUT"
    exit 1
fi

# Step 6: Add OpenAI API key
echo
echo -e "${YELLOW}Step 4: Adding your OpenAI API key${NC}"
echo "You'll need an OpenAI API key to use this proxy."
echo "Get one from: https://platform.openai.com/api-keys"
echo
read -p "Enter your OpenAI API key (sk-...): " OPENAI_KEY

echo "Adding API key to organization..."
KEY_OUTPUT=$(docker exec openai-proxy-api python scripts/manage_api_keys.py create-key "$ORG_ID" "$OPENAI_KEY" --name "Primary Key" 2>&1)
SYNTHETIC_KEY=$(echo "$KEY_OUTPUT" | grep "Synthetic key:" | awk '{print $3}')

if [ -n "$SYNTHETIC_KEY" ]; then
    echo -e "${GREEN}✓ API key added successfully!${NC}"
    echo -e "Synthetic key: ${BLUE}$SYNTHETIC_KEY${NC}"
else
    echo -e "${RED}Error adding API key:${NC}"
    echo "$KEY_OUTPUT"
    exit 1
fi

# Step 7: Generate JWT token
echo
echo -e "${YELLOW}Step 5: Generating JWT token${NC}"
JWT_OUTPUT=$(docker exec openai-proxy-api python scripts/create_jwt.py --org-name "$ORG_NAME" --org-id "$ORG_ID" 2>&1)
JWT_TOKEN=$(echo "$JWT_OUTPUT" | grep -A 1 "JWT Token:" | tail -n 1 | tr -d ' ')

if [ -n "$JWT_TOKEN" ] && [ "$JWT_TOKEN" != "" ]; then
    echo -e "${GREEN}✓ JWT token generated successfully!${NC}"
else
    echo -e "${RED}Error generating JWT token:${NC}"
    echo "$JWT_OUTPUT"
    exit 1
fi

# Step 8: Display summary and next steps
echo
echo -e "${BLUE}======================================"
echo "Setup Complete!"
echo "======================================${NC}"
echo
echo -e "${GREEN}Your credentials:${NC}"
echo -e "Organization: ${BLUE}$ORG_NAME${NC}"
echo -e "Organization ID: ${BLUE}$ORG_ID${NC}"
echo
echo -e "JWT Token:"
echo -e "${YELLOW}$JWT_TOKEN${NC}"
echo
echo -e "${GREEN}Next steps:${NC}"
echo
echo "1. Test the API with curl:"
echo -e "${YELLOW}curl -X POST http://localhost:8000/v1/responses \\"
echo "  -H \"Authorization: Bearer $JWT_TOKEN\" \\"
echo "  -H \"X-User-ID: test-user@example.com\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"model\": \"gpt-4o-mini\", \"input\": \"Hello, world!\", \"max_output_tokens\": 50}'${NC}"
echo
echo "2. View the API documentation:"
echo -e "   ${BLUE}http://localhost:8000/docs${NC}"
echo
echo "3. Run the test suite:"
echo -e "   ${YELLOW}python tests/openai_proxy_test.py${NC}"
echo
echo "4. Check the Python client example:"
echo -e "   ${YELLOW}cat examples/client.py${NC}"
echo
echo -e "${GREEN}Happy coding! 🚀${NC}"