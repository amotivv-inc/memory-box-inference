# Conversation Analysis Guide

This guide explains how to use the conversation analysis feature in the OpenAI Inference Proxy to analyze conversations for intents, sentiments, topics, and custom classifications.

## Overview

The analysis feature allows you to:
- Analyze conversations for intent detection (e.g., support routing)
- Perform sentiment analysis on user messages
- Create custom classification categories
- Save reusable analysis configurations
- Cache results to reduce costs
- Analyze both current and historical conversations

## Key Concepts

### Analysis Configurations
Reusable templates that define:
- Analysis type (intent, sentiment, topic, etc.)
- Categories to classify into
- Model settings (temperature, model choice)
- Output preferences (reasoning, confidence scores)

### Analysis Results
Each analysis returns:
- Primary category detected
- Confidence scores for all categories
- Reasoning for the classification
- Metadata (sentiment, urgency, topics)
- Cost and token usage information

## API Endpoints

### 1. Perform Analysis
```
POST /v1/analysis
```

Analyze a conversation using either a saved configuration or inline configuration.

**Request Body:**
```json
{
  "id": "req_abc123",  // Request ID or Response ID
  "config_id": "550e8400-e29b-41d4-a716-446655440000",  // Optional: saved config
  "config": {  // Optional: inline configuration
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues or bugs",
        "examples": ["app crashes", "error message", "not working"]
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3
  },
  "config_overrides": {  // Optional: override specific fields
    "temperature": 0.5
  }
}
```

### 2. Create Configuration
```
POST /v1/analysis/configs
```

Save a reusable analysis configuration.

**Request Body:**
```json
{
  "name": "Customer Intent Classifier",
  "description": "Classifies customer intents for support routing",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "technical_support",
        "description": "Technical issues, bugs, or errors",
        "examples": ["app crashes", "error message", "not working"]
      },
      {
        "name": "billing_inquiry",
        "description": "Questions about billing or payments",
        "examples": ["charged twice", "cancel subscription", "payment failed"]
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "include_reasoning": true,
    "include_confidence": true,
    "confidence_threshold": 0.7,
    "multi_label": false
  }
}
```

### 3. List Configurations
```
GET /v1/analysis/configs?is_active=true&page=1&page_size=50
```

### 4. Get Configuration
```
GET /v1/analysis/configs/{config_id}
```

### 5. Update Configuration
```
PUT /v1/analysis/configs/{config_id}
```

### 6. Delete Configuration
```
DELETE /v1/analysis/configs/{config_id}
```

## Common Use Cases

### 1. Customer Support Intent Classification
```python
# Create a support intent classifier
config = {
    "name": "Support Intent Classifier",
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
                "description": "New feature suggestions",
                "examples": ["add", "implement", "would be nice", "suggestion"]
            },
            {
                "name": "account_management",
                "description": "Account-related issues",
                "examples": ["login", "password", "email", "profile"]
            }
        ],
        "model": "gpt-4o-mini",
        "temperature": 0.3
    }
}
```

### 2. Sentiment Analysis
```python
# Inline sentiment analysis
analysis_request = {
    "id": "req_123",
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
        ],
        "model": "gpt-4o-mini",
        "temperature": 0.3
    }
}
```

### 3. Urgency Detection
```python
# Detect urgency level for prioritization
urgency_config = {
    "analysis_type": "urgency",
    "categories": [
        {
            "name": "critical",
            "description": "Requires immediate attention",
            "examples": ["emergency", "urgent", "ASAP", "system down"]
        },
        {
            "name": "high",
            "description": "Important but not critical",
            "examples": ["soon", "today", "important", "priority"]
        },
        {
            "name": "medium",
            "description": "Normal priority",
            "examples": ["when possible", "this week", "please help"]
        },
        {
            "name": "low",
            "description": "Can wait",
            "examples": ["no rush", "whenever", "FYI", "just curious"]
        }
    ]
}
```

### 4. Topic Classification
```python
# Classify conversation topics
topic_config = {
    "analysis_type": "topic",
    "categories": [
        {
            "name": "product_features",
            "description": "Discussions about product functionality",
            "examples": ["how does", "feature", "capability", "function"]
        },
        {
            "name": "pricing",
            "description": "Pricing and cost discussions",
            "examples": ["cost", "price", "expensive", "budget"]
        },
        {
            "name": "integration",
            "description": "Integration with other systems",
            "examples": ["API", "integrate", "connect", "webhook"]
        }
    ],
    "multi_label": true  // Can have multiple topics
}
```

## Response Format

### Successful Analysis Response
```json
{
  "request_id": "req_abc123",
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
      "confidence": 0.05,
      "reasoning": null
    }
  ],
  "confidence": 0.92,
  "reasoning": "The user is experiencing technical issues with the application",
  "metadata": {
    "sentiment": "negative",
    "urgency": "high",
    "topics": ["error_handling", "app_stability"]
  },
  "analyzed_at": "2024-01-15T10:30:00Z",
  "model_used": "gpt-4o-mini",
  "tokens_used": 245,
  "cost_usd": 0.000037,
  "cached": false
}
```

## Best Practices

### 1. Category Design
- **Clear Descriptions**: Make category descriptions specific and unambiguous
- **Good Examples**: Provide 3-5 representative examples per category
- **Mutual Exclusivity**: For single-label classification, ensure categories don't overlap
- **Comprehensive Coverage**: Include a "general" or "other" category when needed

### 2. Model Selection
- **gpt-4o-mini**: Fast and cost-effective for most classifications
- **gpt-4o**: Better accuracy for complex or nuanced classifications
- **Temperature**: Use lower values (0.2-0.3) for consistent results

### 3. Configuration Management
- **Reuse Configurations**: Save commonly used configurations for consistency
- **Version Control**: Update configurations rather than creating new ones
- **Naming Convention**: Use descriptive names like "Support_Intent_v2"

### 4. Performance Optimization
- **Caching**: Results are automatically cached for identical analyses
- **Batch Processing**: Analyze multiple conversations with the same config
- **Selective Fields**: Only request fields you need (reasoning, metadata)

## Integration Examples

### Python Client
```python
import httpx
import asyncio

class AnalysisClient:
    def __init__(self, base_url, jwt_token):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }
    
    async def analyze(self, request_id, config_id=None, config=None):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/analysis",
                headers=self.headers,
                json={
                    "id": request_id,
                    "config_id": config_id,
                    "config": config
                }
            )
            return response.json()

# Usage
client = AnalysisClient("https://api.example.com", "your-jwt-token")
result = await client.analyze("req_123", config_id="your-config-id")
```

### JavaScript/TypeScript
```typescript
async function analyzeConversation(
  requestId: string,
  configId?: string,
  config?: AnalysisConfig
): Promise<AnalysisResponse> {
  const response = await fetch('https://api.example.com/v1/analysis', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      id: requestId,
      config_id: configId,
      config: config
    })
  });
  
  return response.json();
}
```

## Troubleshooting

### Common Issues

1. **404 Not Found**
   - Verify the request/response ID exists
   - Check you're using the correct ID format

2. **403 Forbidden**
   - Ensure the request belongs to your organization
   - Verify JWT token is valid

3. **400 Bad Request**
   - Check configuration structure
   - Ensure either config_id or config is provided
   - Validate category definitions

4. **High Costs**
   - Use caching (automatic for identical analyses)
   - Choose appropriate model (gpt-4o-mini vs gpt-4o)
   - Limit token usage with max_tokens setting

### Debugging Tips

1. **Test with Simple Configs**: Start with 2-3 categories
2. **Use Examples**: Test your categories with known inputs
3. **Check Logs**: Review application logs for detailed errors
4. **Validate JSON**: Ensure proper JSON formatting

## Advanced Features

### Custom Prompts
```json
{
  "config": {
    "custom_prompt": "Analyze this conversation:\nUser: {user_input}\nAI: {ai_response}\n\nClassify into: {categories}\n\nProvide detailed reasoning.",
    "categories": [...]
  }
}
```

### Multi-Label Classification
```json
{
  "config": {
    "multi_label": true,
    "confidence_threshold": 0.5,
    "categories": [...]
  }
}
```

### Additional Fields
```json
{
  "config": {
    "additional_fields": {
      "extract_entities": true,
      "detect_language": true,
      "custom_analysis": "specific requirements"
    }
  }
}
```

## Cost Considerations

- **Caching**: Identical analyses return cached results at no additional cost
- **Model Choice**: gpt-4o-mini is ~10x cheaper than gpt-4o
- **Token Usage**: Varies by conversation length and configuration complexity
- **Batch Processing**: No discount, but easier to track costs

## Security

- All analyses are scoped to your organization
- Configurations are private to your organization
- Results are stored encrypted in the database
- JWT authentication required for all endpoints

## Limitations

- Maximum conversation length depends on model context window
- Analysis accuracy depends on category design and examples
- Real-time analysis may add 1-3 seconds latency
- Cached results expire after 30 days (configurable)
