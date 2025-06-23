# Analysis Guide

This guide explains how to use the conversation analysis feature to extract insights from user messages, such as intent, sentiment, and custom classifications.

## Overview

The analysis feature allows you to:

1. Classify user messages into predefined categories
2. Detect user intent
3. Analyze sentiment
4. Extract topics and other metadata
5. Create and manage reusable analysis configurations

## Basic Usage

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
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3
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

## Creating Reusable Configurations

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

## Caching Behavior

By default, each analysis request will perform a fresh analysis, even if you've analyzed the same conversation with the same configuration before. This ensures you always get the most up-to-date results and allows for iterative development of analysis configurations.

If you want to use cached results when available (to save time and reduce costs), you can set the `use_cache` parameter to `true`:

```json
{
  "id": "req_abc123",
  "config_id": "550e8400-e29b-41d4-a716-446655440000",
  "use_cache": true
}
```

When `use_cache` is `true`, the system will:
1. Check if this conversation has been analyzed before with the exact same configuration
2. If found, return the cached result immediately (with `cached: true` in the response)
3. If not found, perform a fresh analysis

This can be useful in production environments to reduce costs and improve response times.

## Updating Configurations

You can update existing configurations at any time:

```http
PUT /v1/analysis/configs/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer YOUR_JWT_TOKEN
X-User-ID: user@example.com
Content-Type: application/json

{
  "name": "Updated Support Intent Classifier",
  "description": "Updated description",
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
      }
    ],
    "model": "gpt-4o-mini",
    "temperature": 0.3
  }
}
```

After updating a configuration, you can immediately use it to analyze conversations, including those that were previously analyzed with the old configuration. The system will perform a fresh analysis with the updated configuration.

## Advanced Configuration Options

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

## Integration Examples

### Python Integration

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
            "config_id": "your-intent-config-id",
            "use_cache": False  # Always perform fresh analysis
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

### JavaScript Integration

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
        config_id: 'your-config-id',
        use_cache: true  // Use cached results when available
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log(`Primary category: ${result.primary_category}`);
      console.log(`Confidence: ${result.confidence * 100}%`);
      console.log(`Cached: ${result.cached ? 'Yes' : 'No'}`);
      
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

## Best Practices

1. **Start with broad categories**: Begin with a few high-level categories and refine as needed
2. **Include examples**: Provide clear examples for each category to improve classification accuracy
3. **Use the right model**: For simple classifications, `gpt-4o-mini` is usually sufficient; for complex analyses, consider `gpt-4o`
4. **Adjust temperature**: Lower values (0.0-0.3) provide more consistent results; higher values allow more creativity
5. **Test and iterate**: Continuously test and refine your configurations based on real-world data
6. **Use caching strategically**: Enable caching in production for efficiency, disable during development for iteration
7. **Monitor costs**: Keep track of token usage and costs, especially for high-volume applications
