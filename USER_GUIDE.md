# Enterprise AI Governance Platform: User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
   - [Organizations](#organizations)
   - [Users](#users)
   - [API Keys](#api-keys)
   - [Sessions](#sessions)
   - [Personas](#personas)
   - [Requests and Responses](#requests-and-responses)
   - [Conversation Context](#conversation-context)
   - [Analysis](#analysis)
   - [Ratings](#ratings)
   - [Analytics](#analytics)
3. [Authentication and Authorization](#authentication-and-authorization)
4. [Making API Requests](#making-api-requests)
5. [Managing Conversations](#managing-conversations)
6. [Using Personas](#using-personas)
7. [Analyzing Conversations](#analyzing-conversations)
8. [Rating Responses](#rating-responses)
9. [Analytics and Monitoring](#analytics-and-monitoring)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## Introduction

The Enterprise AI Governance Platform is a comprehensive solution for governing, securing, and monitoring AI interactions between your applications and OpenAI's Responses API. It provides enterprise-grade features including authentication, user management, usage tracking, analytics, and compliance controls while maintaining full compatibility with OpenAI's API format.

This guide explains the key concepts, features, and patterns of the proxy to help you get the most out of its capabilities.

## Core Concepts

### Organizations

**What they are:** Organizations are the top-level entities in the system. Each organization represents a company, team, or group that uses the proxy.

**How they work:**
- Organizations own all other resources (users, API keys, personas)
- Each organization has its own isolated environment
- JWT tokens are scoped to organizations for authentication
- Usage tracking and analytics are organization-specific

**How to use them:**
- Organizations are created by administrators using the management scripts
- Each organization receives a unique ID used in JWT tokens
- All requests must include a JWT token that identifies the organization

### Users

**What they are:** Users represent individual people or services that interact with the API through your applications.

**How they work:**
- Users belong to organizations
- Users are identified by an external ID (like email, username, or UUID)
- Users can have personal API keys for audit compliance
- Users can have restricted access to specific personas
- User activity is tracked for analytics

**How they're created:**
1. **Automatically:** When a request includes an X-User-ID header for a new user, the system automatically creates the user
2. **Manually:** Administrators can create users with the management scripts or API

**How to use them:**
- Include the X-User-ID header in all API requests
- The X-User-ID can be any string that identifies the user in your system
- The system maintains the mapping between your external user IDs and internal user records

### API Keys

**What they are:** API keys map organizations and users to OpenAI API keys.

**How they work:**
- API keys can be scoped to either:
  - **Organization-wide:** Shared by all users in the organization
  - **User-specific:** Restricted to a particular user
- Real OpenAI API keys are encrypted in the database
- Synthetic keys are generated for reference
- The system automatically selects the appropriate key based on the user making the request

**Key resolution priority:**
1. User-specific key (if exists and active)
2. Organization-wide key (fallback)
3. 403 Forbidden (if no keys available)

**How to use them:**
- You don't need to include API keys in your requests
- The system handles key selection and management
- Administrators can create, manage, and deactivate keys

### Sessions

**What they are:** Sessions group related requests from the same user interaction.

**How they work:**
- Sessions belong to users
- Sessions have a unique session ID
- Sessions can be active or completed
- Sessions track metrics like duration, request count, and token usage
- Sessions provide context for analytics

**How they're created:**
1. **Automatically:** When a request without a session ID is received, a new session is created
2. **Explicitly:** By including an X-Session-ID header in your requests

**How to use them:**
- Include the X-Session-ID header in related requests
- If you don't provide a session ID, one will be generated automatically
- The session ID is returned in the X-Session-ID response header
- Use the same session ID for related requests (e.g., a conversation)
- Sessions are useful for grouping requests in analytics

**How to obtain a session ID:**
- When you make a request without an X-Session-ID header, the response will include an X-Session-ID header with the newly created session ID
- Store this session ID and include it in subsequent related requests
- Example:
  ```
  // First request (no session ID)
  POST /v1/responses
  Headers: Authorization, X-User-ID
  
  // Response headers
  X-Session-ID: sess_abc123def456
  
  // Subsequent requests (include session ID)
  POST /v1/responses
  Headers: Authorization, X-User-ID, X-Session-ID: sess_abc123def456
  ```

### Personas

**What they are:** Personas are reusable system prompts that define the AI's behavior and capabilities.

**How they work:**
- Personas contain system prompt text
- Personas can be organization-wide or user-restricted
- Personas are referenced by ID in requests
- Personas override the instructions field in requests
- Personas have analytics for performance tracking

**How they're created:**
- Through the `/v1/personas` API endpoint
- Using management scripts for administrators

**How to use them:**
- Include the `persona_id` field in your request body
- The system will use the persona's content as the system prompt
- If both `persona_id` and `instructions` are provided, the persona takes precedence
- Example:
  ```json
  {
    "model": "gpt-4o",
    "input": "Hello, how can you help me?",
    "persona_id": "123e4567-e89b-12d3-a456-426614174000"
  }
  ```

### Requests and Responses

**What they are:** Requests are individual API calls to the proxy, and responses are the corresponding replies from OpenAI.

**How they work:**
- Each request has a unique request ID
- Each OpenAI response has a response ID
- Requests are associated with users and sessions
- Requests can use personas for system prompts
- Requests can be streaming or non-streaming
- Usage data (tokens, cost) is tracked for each request
- Requests can be rated by users

**Request flow:**
1. Client sends request with JWT token and user ID
2. Proxy authenticates and authorizes the request
3. Proxy selects the appropriate API key
4. Proxy forwards the request to OpenAI
5. Proxy receives and processes the response
6. Proxy logs usage data
7. Proxy returns the response to the client

**How to use them:**
- Make POST requests to `/v1/responses`
- Include required headers (Authorization, X-User-ID)
- Optionally include X-Session-ID for session tracking
- Format request body according to OpenAI's Responses API
- Handle streaming or non-streaming responses as needed

### Conversation Context

**What they are:** Conversation context allows the AI to remember previous interactions within a conversation.

**How they work:**
- OpenAI's Responses API uses the `previous_response_id` field to maintain context
- The proxy passes this field to OpenAI and stores response IDs
- This allows for multi-turn conversations without sending the entire history
- The proxy doesn't automatically manage conversation history - your client application must handle this

**How to use them:**
1. Send your initial request without a `previous_response_id`
2. Extract the response ID from OpenAI's response (`response.id`)
3. For follow-up messages, include this ID as `previous_response_id`
4. Example:
   ```json
   // First message
   {
     "model": "gpt-4o",
     "input": "What is quantum computing?"
   }
   
   // Response contains ID: resp_abc123
   
   // Follow-up message
   {
     "model": "gpt-4o",
     "input": "Explain that in simpler terms",
     "previous_response_id": "resp_abc123"
   }
   ```

**Important notes:**
- The proxy's session tracking (X-Session-ID header) is separate from conversation context
- Sessions are used for analytics and grouping, while `previous_response_id` is for AI memory
- Response IDs are stored in the proxy's database and can be retrieved with the request ID if needed

### Analysis

**What it is:** Analysis is a powerful feature that extracts insights from conversations, such as user intent, sentiment, and custom classifications.

**How it works:**
- Analysis uses OpenAI models to classify conversations into predefined categories
- Analysis can be performed on any request or response
- Analysis configurations define the categories and classification parameters
- Analysis results include confidence scores and reasoning
- Analysis results are cached to improve performance and reduce costs

**Types of analysis:**
- **Intent detection**: Classify user messages by their purpose (e.g., technical support, billing inquiry)
- **Sentiment analysis**: Determine if messages are positive, negative, or neutral
- **Topic classification**: Identify the main topics discussed in a conversation
- **Custom classification**: Create your own categories for specialized needs

**How to use it:**
1. Create a conversation using the `/v1/responses` endpoint
2. Get the request ID or response ID from the response
3. Send an analysis request to `/v1/analysis` with the ID and configuration
4. Process the analysis results in your application

**Example:**
```json
// Analysis request
{
  "id": "req_abc123def456",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues requiring engineering help",
        "examples": ["bug", "error", "crash", "not working"]
      },
      {
        "name": "billing_inquiry",
        "description": "Billing and payment questions",
        "examples": ["invoice", "charge", "payment", "subscription"]
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3
  }
}

// Analysis response
{
  "request_id": "req_abc123def456",
  "response_id": "resp_xyz789",
  "analysis_type": "intent",
  "primary_category": "technical_support",
  "categories": [
    {
      "name": "technical_support",
      "confidence": 0.92,
      "reasoning": "User mentions app crashes and error messages"
    },
    {
      "name": "billing_inquiry",
      "confidence": 0.05
    }
  ],
  "confidence": 0.92,
  "reasoning": "The user is experiencing technical issues with the application",
  "metadata": {
    "sentiment": "frustrated",
    "urgency": "high",
    "topics": ["error_handling", "app_stability"]
  },
  "analyzed_at": "2025-06-23T15:30:45Z",
  "model_used": "gpt-4o-mini",
  "tokens_used": 320,
  "cost_usd": 0.000048,
  "cached": false
}
```

**Configuration management:**
- Save reusable configurations with the `/v1/analysis/configs` endpoint
- Retrieve configurations by ID or name
- Use saved configurations by referencing their ID in analysis requests
- Override specific fields in saved configurations as needed

**Benefits:**
- **Routing**: Automatically route conversations to the right team or system
- **Prioritization**: Identify urgent issues that need immediate attention
- **Analytics**: Gain insights into common user intents and sentiments
- **Integration**: Connect with CRM, ticketing, or support systems based on intent
- **Personalization**: Tailor experiences based on detected user needs

### Ratings

**What they are:** Ratings allow users to provide feedback on AI responses.

**How they work:**
- Users can rate responses with thumbs up (1) or thumbs down (-1)
- Ratings can include optional text feedback
- Ratings are stored with the request record
- Ratings can be analyzed for quality assessment
- Ratings can be submitted using either request ID or response ID

**How to use them:**
- Make POST requests to `/v1/responses/{id}/rate`
- The ID can be either a request ID (req_xxx) or response ID (resp_xxx)
- Include a rating value (1 for positive, -1 for negative)
- Optionally include feedback text
- Example:
  ```json
  {
    "rating": 1,
    "feedback": "This response was very helpful and accurate."
  }
  ```

### Analytics

**What they are:** Analytics provide insights into API usage, performance, and costs.

**How they work:**
- The proxy tracks detailed metrics for all requests
- Analytics are scoped to organizations
- Analytics can be filtered by user, date range, model, etc.
- Analytics include token usage, costs, success rates, and more
- Analytics are available through dedicated API endpoints

**Available analytics:**
1. **Model Usage**: Statistics by model
2. **Rated Responses**: List of rated responses with details
3. **User Usage**: Statistics by user
4. **Sessions**: Session analytics
5. **Persona Usage**: Statistics by persona
6. **Persona Details**: Detailed analytics for a specific persona

**How to use them:**
- Make GET requests to the analytics endpoints
- Include JWT token for authentication
- Use query parameters for filtering
- Example:
  ```
  GET /v1/analytics/models?start_date=2025-06-01&end_date=2025-06-07
  ```

## Authentication and Authorization

### JWT Authentication

The proxy uses JWT (JSON Web Token) for authentication. Each token is associated with an organization.

**How it works:**
1. Administrators generate JWT tokens for organizations
2. Clients include the token in the Authorization header
3. The proxy validates the token and identifies the organization
4. If the token is valid, the request is processed

**How to use it:**
- Include the JWT token in the Authorization header:
  ```
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
- Tokens have an expiration date (typically 365 days)
- Store tokens securely in your application

### User Identification

In addition to JWT authentication, the proxy requires user identification for all requests.

**How it works:**
1. Clients include a user identifier in the X-User-ID header
2. The proxy finds or creates the user in the database
3. The user is associated with the request for tracking and analytics
4. If the user has a personal API key, it will be used

**How to use it:**
- Include the X-User-ID header in all requests:
  ```
  X-User-ID: user@example.com
  ```
- The user ID can be any string that identifies the user in your system
- If the user doesn't exist, they will be created automatically
- Users are always scoped to organizations

## Making API Requests

### Basic Request Structure

```http
POST /v1/responses
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
X-Session-ID: session123 (optional)
Content-Type: application/json

{
  "model": "gpt-4o",
  "input": "Your prompt here",
  "stream": false,
  "temperature": 0.7,
  "max_output_tokens": 150
}
```

### Response Structure

```json
{
  "id": "resp_abc123def456",
  "content": [
    {
      "text": "This is the response from the AI model."
    }
  ],
  "usage": {
    "input_tokens": 10,
    "output_tokens": 50,
    "total_tokens": 60
  }
}
```

### Response Headers

```
X-Request-ID: req_abc123def456
X-Session-ID: session123
```

### Streaming Requests

For streaming responses, set `stream: true` in your request body. The response will be a stream of Server-Sent Events (SSE).

```javascript
const response = await fetch('/v1/responses', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'X-User-ID': 'user@example.com',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o',
    input: 'Your prompt here',
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.content) {
        console.log(data.content[0].text);
      }
    }
  }
}
```

## Managing Conversations

### Starting a Conversation

To start a new conversation, make a request without a `previous_response_id`:

```json
{
  "model": "gpt-4o",
  "input": "What is quantum computing?",
  "stream": false
}
```

Save the response ID from the response:

```json
{
  "id": "resp_abc123def456",
  "content": [
    {
      "text": "Quantum computing is a type of computation that harnesses quantum mechanical phenomena..."
    }
  ],
  "usage": {
    "input_tokens": 5,
    "output_tokens": 50,
    "total_tokens": 55
  }
}
```

### Continuing a Conversation

To continue the conversation, include the previous response ID in your next request:

```json
{
  "model": "gpt-4o",
  "input": "Can you explain that in simpler terms?",
  "previous_response_id": "resp_abc123def456",
  "stream": false
}
```

### Session Management

While conversation context is maintained through `previous_response_id`, sessions provide a way to group related requests for analytics and tracking.

To create a session:
1. Make a request without an X-Session-ID header
2. The response will include an X-Session-ID header
3. Use this session ID for all related requests

```http
// First request
POST /v1/responses
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com

// Response headers
X-Request-ID: req_abc123def456
X-Session-ID: sess_abc123def456

// Subsequent requests
POST /v1/responses
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
X-Session-ID: sess_abc123def456
```

Sessions are automatically tracked and can be analyzed through the analytics endpoints.

## Using Personas

### Creating a Persona

```http
POST /v1/personas
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "name": "Customer Support Agent",
  "content": "You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful.",
  "description": "For handling customer inquiries"
}
```

Response:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "organization_id": "123e4567-e89b-12d3-a456-426614174001",
  "user_id": null,
  "name": "Customer Support Agent",
  "description": "For handling customer inquiries",
  "content": "You are a helpful customer support agent for Acme Inc. You should be polite, professional, and helpful.",
  "is_active": true,
  "created_at": "2025-06-01T12:00:00.000Z",
  "updated_at": "2025-06-01T12:00:00.000Z"
}
```

### Using a Persona in a Request

```http
POST /v1/responses
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "model": "gpt-4o",
  "input": "I'm having trouble with my order",
  "persona_id": "123e4567-e89b-12d3-a456-426614174000",
  "stream": false
}
```

### Listing Available Personas

```http
GET /v1/personas
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

### Updating a Persona

```http
PUT /v1/personas/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "name": "Updated Customer Support Agent",
  "content": "Updated system prompt content",
  "description": "Updated description"
}
```

### Persona Analytics

```http
GET /v1/analytics/personas/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

## Analyzing Conversations

The Analysis feature allows you to extract valuable insights from user messages, such as intent, sentiment, and custom classifications. This section explains how to use this feature effectively.

### Basic Analysis

To analyze a conversation:

1. First, create a conversation using the `/v1/responses` endpoint
2. Get the request ID or response ID from the response
3. Send an analysis request to the `/v1/analysis` endpoint

```http
POST /v1/analysis
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "id": "req_abc123def456",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues requiring engineering help",
        "examples": ["bug", "error", "crash", "not working"]
      },
      {
        "name": "billing_inquiry",
        "description": "Billing and payment questions",
        "examples": ["invoice", "charge", "payment", "subscription"]
      },
      {
        "name": "feature_request",
        "description": "Requests for new features",
        "examples": ["add feature", "would be nice if", "suggestion"]
      },
      {
        "name": "general_inquiry",
        "description": "General questions about the product",
        "examples": ["how do I", "where is", "what is"]
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "include_reasoning": true
  }
}
```

The response will include the primary category, confidence scores, and reasoning:

```json
{
  "request_id": "req_abc123def456",
  "response_id": "resp_xyz789",
  "analysis_type": "intent",
  "primary_category": "technical_support",
  "categories": [
    {
      "name": "technical_support",
      "confidence": 0.92,
      "reasoning": "User mentions app crashes and error messages"
    },
    {
      "name": "billing_inquiry",
      "confidence": 0.05
    },
    {
      "name": "feature_request",
      "confidence": 0.02
    },
    {
      "name": "general_inquiry",
      "confidence": 0.01
    }
  ],
  "confidence": 0.92,
  "reasoning": "The user is experiencing technical issues with the application",
  "metadata": {
    "sentiment": "frustrated",
    "urgency": "high",
    "topics": ["error_handling", "app_stability"]
  },
  "analyzed_at": "2025-06-23T15:30:45Z",
  "model_used": "gpt-4o-mini",
  "tokens_used": 320,
  "cost_usd": 0.000048,
  "cached": false
}
```

### Creating Reusable Configurations

For repeated analyses with the same categories, create a reusable configuration:

```http
POST /v1/analysis/configs
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "name": "Support Intent Classifier",
  "description": "Classifies customer support requests by intent",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues requiring engineering help",
        "examples": ["bug", "error", "crash", "not working"]
      },
      {
        "name": "billing_inquiry",
        "description": "Billing and payment questions",
        "examples": ["invoice", "charge", "payment", "subscription"]
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3
  }
}
```

Then use the saved configuration by its ID:

```http
POST /v1/analysis
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "id": "req_def456",
  "config_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

You can also retrieve a configuration by name:

```http
GET /v1/analysis/configs/by-name/Support%20Intent%20Classifier
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

### Intent Detection Example

Intent detection is useful for routing conversations to the appropriate team or system. For example, to detect if a user needs technical support or has a billing question:

```http
POST /v1/analysis
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "id": "req_abc123def456",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues requiring engineering help",
        "examples": ["bug", "error", "crash", "not working"]
      },
      {
        "name": "billing_inquiry",
        "description": "Billing and payment questions",
        "examples": ["invoice", "charge", "payment", "subscription"]
      }
    ]
  }
}
```

Based on the result, you can route the conversation to the appropriate team:

```javascript
// Example JavaScript code for routing
async function routeConversation(requestId) {
  const analysisResponse = await fetch('/v1/analysis', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_JWT_TOKEN',
      'X-User-ID': 'user@example.com',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      id: requestId,
      config_id: 'your-intent-config-id'
    })
  });
  
  const analysis = await analysisResponse.json();
  
  switch (analysis.primary_category) {
    case 'technical_support':
      return routeToTechnicalSupport(requestId);
    case 'billing_inquiry':
      return routeToBillingTeam(requestId);
    default:
      return routeToGeneralSupport(requestId);
  }
}
```

### Sentiment Analysis

Sentiment analysis helps identify the emotional tone of a message:

```http
POST /v1/analysis
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "id": "req_abc123def456",
  "config": {
    "analysis_type": "sentiment",
    "categories": [
      {
        "name": "positive",
        "description": "Positive sentiment",
        "examples": ["great", "love it", "excellent", "thank you"]
      },
      {
        "name": "neutral",
        "description": "Neutral sentiment",
        "examples": ["okay", "fine", "alright", "understood"]
      },
      {
        "name": "negative",
        "description": "Negative sentiment",
        "examples": ["bad", "terrible", "frustrated", "disappointed"]
      }
    ]
  }
}
```

### Advanced Configuration Options

The analysis feature supports several advanced options:

- **Custom Prompts**: Provide a custom prompt template for specialized analysis
- **Multi-label Classification**: Allow multiple primary categories
- **Confidence Threshold**: Set a minimum confidence threshold
- **Model Selection**: Choose between different OpenAI models
- **Temperature**: Adjust the randomness of the analysis

Example with advanced options:

```http
POST /v1/analysis
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "id": "req_abc123def456",
  "config": {
    "analysis_type": "custom",
    "categories": [
      {"name": "urgent", "description": "Requires immediate attention"},
      {"name": "important", "description": "Important but not urgent"},
      {"name": "routine", "description": "Regular inquiry"}
    ],
    "model": "gpt-4o",
    "temperature": 0.2,
    "multi_label": true,
    "confidence_threshold": 0.5,
    "custom_prompt": "Analyze this conversation and determine the urgency level:\n\nUser: {user_input}\nAI: {ai_response}\n\nCategories: {categories}\n\nProvide detailed reasoning."
  }
}
```

### Caching and Performance

Analysis results are automatically cached to improve performance and reduce costs. When you analyze the same request with the same configuration, the cached result is returned:

```json
{
  "request_id": "req_abc123def456",
  "response_id": "resp_xyz789",
  "analysis_type": "intent",
  "primary_category": "technical_support",
  "categories": [...],
  "confidence": 0.92,
  "reasoning": "The user is experiencing technical issues with the application",
  "metadata": {...},
  "analyzed_at": "2025-06-23T15:30:45Z",
  "model_used": "gpt-4o-mini",
  "tokens_used": 320,
  "cost_usd": 0.000048,
  "cached": true
}
```

### Integration Examples

#### Python Integration

```python
import requests

def analyze_intent(request_id, jwt_token, user_id):
    response = requests.post(
        "http://localhost:8000/v1/analysis",
        headers={
            "Authorization": f"Bearer {jwt_token}",
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "id": request_id,
            "config_id": "your-intent-config-id"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Primary intent: {result['primary_category']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Reasoning: {result['reasoning']}")
        return result
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
```

#### JavaScript Integration

```javascript
async function analyzeConversation(requestId) {
  try {
    const response = await fetch('http://localhost:8000/v1/analysis', {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer YOUR_JWT_TOKEN',
        'X-User-ID': 'user@example.com',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        id: requestId,
        config_id: 'your-config-id'
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log(`Primary category: ${result.primary_category}`);
      console.log(`Confidence: ${result.confidence * 100}%`);
      
      // Take action based on intent
      if (result.primary_category === 'technical_support' && result.confidence > 0.8) {
        // Route to technical support
      }
      
      return result;
    } else {
      console.error(`Error: ${response.status}`);
      console.error(await response.text());
      return null;
    }
  } catch (error) {
    console.error('Analysis failed:', error);
    return null;
  }
}
```

## Rating Responses

### Rating by Request ID

```http
POST /v1/responses/req_abc123def456/rate
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "rating": 1,
  "feedback": "This response was very helpful and accurate."
}
```

### Rating by Response ID

```http
POST /v1/responses/resp_abc123def456/rate
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "rating": -1,
  "feedback": "This response didn't answer my question."
}
```

### Viewing Rated Responses

```http
GET /v1/analytics/rated-responses
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

## Analytics and Monitoring

### Model Usage Analytics

```http
GET /v1/analytics/models
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

Response:

```json
{
  "models": [
    {
      "model": "gpt-4o",
      "request_count": 150,
      "success_count": 145,
      "failure_count": 5,
      "success_rate": 96.7,
      "input_tokens": 15000,
      "output_tokens": 45000,
      "total_tokens": 60000,
      "total_cost": 1.25,
      "avg_response_time": 1.5
    }
  ],
  "total_requests": 200,
  "total_cost": 2.50,
  "period_start": "2025-06-01T00:00:00Z",
  "period_end": "2025-06-07T23:59:59Z"
}
```

### User Usage Analytics

```http
GET /v1/analytics/user-usage
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

Response:

```json
{
  "users": [
    {
      "user_id": "user123",
      "request_count": 150,
      "success_count": 145,
      "failure_count": 5,
      "success_rate": 96.7,
      "input_tokens": 15000,
      "output_tokens": 45000,
      "total_tokens": 60000,
      "total_cost": 1.25,
      "avg_response_time": 1.5,
      "last_request_at": "2025-06-01T12:34:56Z",
      "models_used": ["gpt-4o", "gpt-4o-mini"]
    }
  ],
  "total_users": 10,
  "total_requests": 200,
  "total_cost": 2.50,
  "period_start": "2025-06-01T00:00:00Z",
  "period_end": "2025-06-07T23:59:59Z",
  "filtered_by_user": "user123"
}
```

### Session Analytics

```http
GET /v1/analytics/sessions
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

Response:

```json
{
  "sessions": [
    {
      "session_id": "sess_1234567890abcdef",
      "user_id": "user123",
      "started_at": "2025-06-01T12:00:00Z",
      "ended_at": "2025-06-01T12:30:00Z",
      "duration_minutes": 30.5,
      "request_count": 15,
      "total_tokens": 5000,
      "total_cost": 0.25,
      "models_used": ["gpt-4o", "gpt-4o-mini"],
      "is_active": false
    }
  ],
  "total_sessions": 100,
  "active_sessions": 25,
  "total_requests": 1500,
  "total_cost": 25.50,
  "avg_session_duration": 15.3,
  "period_start": "2025-06-01T00:00:00Z",
  "period_end": "2025-06-07T23:59:59Z",
  "filtered_by_user": "user123"
}
```

### Persona Analytics

```http
GET /v1/analytics/personas
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

Response:

```json
{
  "personas": [
    {
      "persona_id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Customer Support Agent",
      "description": "For handling customer inquiries",
      "user_id": null,
      "request_count": 150,
      "success_count": 145,
      "failure_count": 5,
      "success_rate": 96.7,
      "input_tokens": 15000,
      "output_tokens": 45000,
      "total_tokens": 60000,
      "total_cost": 1.25,
      "avg_response_time": 1.5,
      "last_used_at": "2025-06-01T12:34:56Z",
      "models_used": ["gpt-4o", "gpt-4o-mini"],
      "is_active": true
    }
  ],
  "total_personas": 10,
  "total_requests": 200,
  "total_cost": 2.50,
  "period_start": "2025-06-01T00:00:00Z",
  "period_end": "2025-06-07T23:59:59Z",
  "filtered_by_user": "user123",
  "include_inactive": false
}
```

### Detailed Persona Analytics

```http
GET /v1/analytics/personas/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
```

Response:

```json
{
  "persona": {
    "persona_id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Customer Support Agent",
    "description": "For handling customer inquiries",
    "user_id": null,
    "request_count": 150,
    "success_count": 145,
    "failure_count": 5,
    "success_rate": 96.7,
    "input_tokens": 15000,
    "output_tokens": 45000,
    "total_tokens": 60000,
    "total_cost": 1.25,
    "avg_response_time": 1.5,
    "last_used_at": "2025-06-01T12:34:56Z",
    "models_used": ["gpt-4o", "gpt-4o-mini"],
    "is_active": true
  },
  "daily_usage": [
    {
      "date": "2025-06-01",
      "request_count": 25,
      "success_count": 24,
      "failure_count": 1,
      "total_tokens": 10000,
      "total_cost": 0.25
    }
  ],
  "request_count_by_model": {
    "gpt-4o": 100,
    "gpt-4o-mini": 50
  },
  "request_count_by_status": {
    "completed": 145,
    "failed": 5
  },
  "token_usage_by_model": {
    "gpt-4o": {
      "input_tokens": 10000,
      "output_tokens": 30000,
      "total_tokens": 40000,
      "total_cost": 1.00
    },
    "gpt-4o-mini": {
      "input_tokens": 5000,
      "output_tokens": 15000,
      "total_tokens": 20000,
      "total_cost": 0.25
    }
  },
  "top_users": [
    {
      "user_id": "user123",
      "request_count": 75,
      "total_tokens": 30000,
      "total_cost": 0.75
    }
  ],
  "period_start": "2025-06-01T00:00:00Z",
  "period_end": "2025-06-07T23:59:59Z"
}
```

## Best Practices

### Authentication and Security

1. **Store JWT tokens securely** - Don't commit them to version control
2. **Handle token expiration** - Implement token refresh logic
3. **Use HTTPS in production** - Always encrypt traffic in transit
4. **Validate user input** - Sanitize all user input before sending to the API

### Performance and Reliability

1. **Implement retry logic** - For transient network errors
2. **Handle streaming properly** - Use appropriate streaming libraries
3. **Monitor usage** - Track token consumption and costs
4. **Implement timeouts** - Set appropriate timeouts for requests

### User Experience

1. **Use sessions effectively** - Group related requests for better tracking
2. **Collect ratings** - Encourage users to rate responses for quality improvement
3. **Leverage personas** - Create specialized personas for different use cases
4. **Monitor persona performance** - Use analytics to optimize your personas

### Conversation Management

1. **Store response IDs** - Save response IDs for conversation continuity
2. **Use previous_response_id** - Include previous response IDs for follow-up messages
3. **Manage session context** - Use the same session ID for related requests
4. **Handle errors gracefully** - Provide meaningful error messages to users

## Troubleshooting

### Common Issues

#### "No active API key found for organization"
- Verify organization has at least one active API key
- Check if user-specific key exists (if applicable)
- Ensure API key is marked as active

#### "Invalid authentication credentials"
- Verify JWT token is valid and not expired
- Check JWT_SECRET_KEY matches between token generation and validation
- Ensure Authorization header format is correct: `Bearer <token>`

#### "User not found"
- Users are auto-created on first request
- For manual creation, ensure organization ID is correct
- Check X-User-ID header is present in requests

#### "Persona not found or not accessible"
- Verify persona ID is correct
- Check if persona is active
- Ensure user has access to the persona (if user-restricted)

#### "Error processing request"
- Check request format matches OpenAI's Responses API
- Verify model name is valid
- Ensure input is properly formatted

### Getting Help

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/amotivv-inc/enterprise-ai-governance/issues)
- 💬 [Discussions](https://github.com/amotivv-inc/enterprise-ai-governance/discussions)
- 📧 Email: ai@amotivv.com

## License

This software is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). This license requires that all modified versions must be released under the same license. Additionally, if you run a modified version of this software on a server and allow users to interact with it, you must make the source code available to those users.

For more information about the AGPL-3.0 license, visit: https://www.gnu.org/licenses/agpl-3.0.html
