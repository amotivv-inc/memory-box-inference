# Conversation Analysis API Guide

This guide explains how to use the Conversation Analysis API to extract insights from user messages, such as intent, sentiment, and other classifications.

## Table of Contents

1. [Overview](#overview)
2. [Creating an Analysis Configuration](#creating-an-analysis-configuration)
3. [Analyzing a Conversation](#analyzing-a-conversation)
4. [Understanding Analysis Results](#understanding-analysis-results)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

## Overview

The Conversation Analysis API allows you to:

- Classify user messages into predefined categories
- Detect user intent (e.g., wanting to speak with a human agent)
- Analyze sentiment (positive, negative, neutral)
- Extract topics and other metadata
- Create and reuse analysis configurations

This is particularly useful for:
- Routing conversations to the right team
- Prioritizing urgent requests
- Understanding user needs
- Improving response quality

## Creating an Analysis Configuration

Analysis configurations define how conversations should be analyzed. By creating reusable configurations, you can ensure consistent analysis across your application.

### API Endpoint

```
POST /v1/analysis/configs
```

### Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
x-user-id: YOUR_USER_ID
Content-Type: application/json
```

### Request Body

```json
{
  "name": "User Intent Test",
  "description": "Get user intent from web chat",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "contact_human",
        "description": "User wants to speak with a human agent",
        "examples": ["speak to a person", "talk to a human", "agent please"]
      },
      {
        "name": "book_meeting",
        "description": "User wants to schedule a meeting with a human",
        "examples": ["schedule callback", "schedule a meeting", "call me back later"]
      }
    ],
    "model": "gpt-4o",
    "temperature": 0.3,
    "include_reasoning": true,
    "include_confidence": true,
    "confidence_threshold": 0.7,
    "max_tokens": 0,
    "multi_label": false
  }
}
```

### Key Parameters Explained

- **name**: A unique name for your configuration
- **description**: A description of what this configuration analyzes
- **analysis_type**: The type of analysis (intent, sentiment, topic, etc.)
- **categories**: The categories to classify messages into
  - **name**: Short identifier for the category
  - **description**: Detailed explanation of what the category represents
  - **examples**: Sample phrases that would fall into this category
- **model**: The OpenAI model to use (e.g., gpt-4o, gpt-4o-mini)
- **temperature**: Controls randomness (0.0-1.0, lower is more deterministic)
- **include_reasoning**: Whether to include reasoning for classifications
- **include_confidence**: Whether to include confidence scores
- **confidence_threshold**: Minimum confidence to consider a classification valid
- **multi_label**: Whether multiple primary categories can be assigned

### Example Request (curl)

```bash
curl -X 'POST' \
  'https://your-api-endpoint/v1/analysis/configs' \
  -H 'accept: application/json' \
  -H 'x-user-id: your-user-id' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "User Intent Test",
  "description": "Get user intent from web chat",
  "config": {
    "analysis_type": "intent",
    "categories": [
      {
        "name": "contact_human",
        "description": "User wants to speak with a human agent",
        "examples": ["speak to a person", "talk to a human", "agent please"]
      },
      {
        "name": "book_meeting",
        "description": "User wants to schedule a meeting with a human",
        "examples": ["schedule callback", "schedule a meeting", "call me back later"]
      }
    ],
    "model": "gpt-4o",
    "temperature": 0.3,
    "include_reasoning": true,
    "include_confidence": true,
    "confidence_threshold": 0.7,
    "max_tokens": 0,
    "multi_label": false
  }
}'
```

### Example Response

```json
{
  "id": "0e2e2f2c-2d50-43b9-af09-310ae3fdbb58",
  "organization_id": "5ec7fc3b-5840-43cf-be15-6920ea35547a",
  "name": "User Intent Test",
  "description": "Get user intent from web chat",
  "config": {
    "model": "gpt-4o",
    "categories": [
      {
        "name": "contact_human",
        "examples": [
          "speak to a person",
          "talk to a human",
          "agent please"
        ],
        "description": "User wants to speak with a human agent"
      },
      {
        "name": "book_meeting",
        "examples": [
          "schedule callback",
          "schedule a meeting",
          "call me back later"
        ],
        "description": "User wants to schedule a meeting with a human"
      }
    ],
    "max_tokens": 0,
    "multi_label": false,
    "temperature": 0.3,
    "analysis_type": "intent",
    "custom_prompt": null,
    "additional_fields": null,
    "include_reasoning": true,
    "include_confidence": true,
    "confidence_threshold": 0.7
  },
  "is_active": true,
  "created_by": "6b5441b3-c71a-4c20-88d1-3a474be473e2",
  "created_at": "2025-06-24T18:04:48.819186Z",
  "updated_at": "2025-06-24T18:04:48.819186Z"
}
```

**Important**: Save the `id` from the response. You'll need it to use this configuration for analysis.

## Analyzing a Conversation

Once you have created an analysis configuration, you can use it to analyze conversations.

### API Endpoint

```
POST /v1/analysis
```

### Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
x-user-id: YOUR_USER_ID
Content-Type: application/json
```

### Request Body

```json
{
  "id": "resp_RESPONSE_ID_OR_REQUEST_ID",
  "config_id": "YOUR_CONFIG_ID",
  "config_overrides": {},
  "use_cache": false
}
```

### Key Parameters Explained

- **id**: The ID of the response or request to analyze
- **config_id**: The ID of the analysis configuration to use
- **config_overrides**: Optional overrides for specific configuration parameters
- **use_cache**: Whether to use cached results if available

### Example Request (curl)

```bash
curl -X 'POST' \
  'https://your-api-endpoint/v1/analysis' \
  -H 'accept: application/json' \
  -H 'x-user-id: your-user-id' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "resp_685ad7cc45a881a29612f39ab9db54b1037e766545fcdb76",
  "config_id": "0e2e2f2c-2d50-43b9-af09-310ae3fdbb58",
  "config_overrides": {},
  "use_cache": false
}'
```

### Example Response

```json
{
  "request_id": "req_200dff618cdb47a5a0e6743a644c1bda",
  "response_id": "resp_685ad7cc45a881a29612f39ab9db54b1037e766545fcdb76",
  "analysis_type": "intent",
  "primary_category": "contact_human",
  "categories": [
    {
      "name": "contact_human",
      "confidence": 0,
      "reasoning": null
    },
    {
      "name": "book_meeting",
      "confidence": 0,
      "reasoning": null
    }
  ],
  "confidence": 0,
  "reasoning": "The conversation does not indicate any desire to speak with a human agent or schedule a meeting. The user simply requested information, which was provided by the AI.",
  "metadata": {
    "topics": [
      "Plaid services",
      "applications",
      "financial technology"
    ],
    "urgency": "low",
    "sentiment": "neutral"
  },
  "analyzed_at": "2025-06-24T18:07:10.975435Z",
  "model_used": "gpt-4o",
  "tokens_used": 601,
  "cost_usd": 0.001503,
  "cached": false
}
```

## Understanding Analysis Results

The analysis response contains valuable information about the conversation:

- **primary_category**: The most likely category for the conversation
- **categories**: All categories with their confidence scores
- **confidence**: Overall confidence in the classification
- **reasoning**: Explanation of why this classification was chosen
- **metadata**: Additional information like sentiment, urgency, and topics
- **tokens_used**: Number of tokens used for the analysis
- **cost_usd**: Cost of the analysis in USD

### Interpreting Confidence Scores

Confidence scores range from 0.0 to 1.0:
- **0.9-1.0**: Very high confidence
- **0.7-0.9**: High confidence
- **0.5-0.7**: Moderate confidence
- **0.3-0.5**: Low confidence
- **0.0-0.3**: Very low confidence

### Using the Results

Based on the analysis results, you can:

1. **Route conversations**: Send to human agents when "contact_human" is detected
2. **Prioritize**: Handle high urgency conversations first
3. **Personalize**: Adjust responses based on sentiment
4. **Track trends**: Monitor common topics and intents over time

## Best Practices

### Creating Effective Configurations

1. **Start with clear categories**: Define categories that are distinct and meaningful
2. **Provide good examples**: Include 3-5 diverse examples for each category
3. **Use appropriate models**: 
   - gpt-4o for highest accuracy
   - gpt-4o-mini for good balance of cost and accuracy
4. **Set reasonable thresholds**: Start with 0.7 and adjust based on results

### Optimizing Analysis

1. **Use caching**: Set `use_cache: true` for repeated analyses
2. **Analyze selectively**: Only analyze conversations where insights are valuable
3. **Monitor costs**: Track token usage and adjust models as needed
4. **Iterate on configurations**: Refine categories and examples based on results

## Troubleshooting

### Common Issues

#### Invalid JSON
Ensure your JSON is valid with no trailing commas or syntax errors.

#### Configuration Not Found
Verify the `config_id` is correct and the configuration is active.

#### Response/Request Not Found
Ensure the response or request ID exists and is accessible to your organization.

#### Low Confidence Scores
- Add more examples to your categories
- Make category descriptions more detailed
- Consider adjusting the confidence threshold

#### High Costs
- Use gpt-4o-mini instead of gpt-4o
- Enable caching for repeated analyses
- Analyze only when necessary

### Getting Help

If you encounter issues not covered here, contact support at support@example.com.
