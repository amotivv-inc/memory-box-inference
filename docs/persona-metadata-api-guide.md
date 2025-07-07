# Persona Metadata API Guide

This guide explains how to use the Persona Metadata system to organize, version, and manage your personas with flexible metadata fields.

## Table of Contents

1. [Overview](#overview)
2. [Creating Personas with Metadata](#creating-personas-with-metadata)
3. [Searching and Filtering by Metadata](#searching-and-filtering-by-metadata)
4. [Updating Persona Metadata](#updating-persona-metadata)
5. [Using Personas with Metadata in Responses API](#using-personas-with-metadata-in-responses-api)
6. [Analytics Integration](#analytics-integration)
7. [Use Cases and Examples](#use-cases-and-examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The Persona Metadata system allows you to:

- Add structured metadata to personas for organization and versioning
- Search and filter personas by any metadata criteria
- Track persona lifecycle (development, testing, production)
- Organize personas by team, department, or project
- Integrate with external workflows and tools
- Maintain backward compatibility with existing personas

This is particularly useful for:
- Version control and approval workflows
- Environment-specific persona deployment
- Team-based persona organization
- A/B testing and experimentation
- Integration with external systems

## Creating Personas with Metadata

### API Endpoint

```
POST /v1/personas
```

### Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
x-user-id: YOUR_USER_ID (optional, for user-restricted personas)
Content-Type: application/json
```

### Request Body

```json
{
  "name": "Customer Support Agent v2.1",
  "description": "Enhanced customer support persona with improved empathy",
  "content": "You are a helpful and empathetic customer support agent...",
  "metadata": {
    "tags": ["production", "approved", "customer-support"],
    "version": "2.1.0",
    "status": "production",
    "department": "customer_success",
    "environment": "production",
    "created_by": "team-lead@company.com",
    "approved_by": "manager@company.com",
    "approval_date": "2025-01-15T10:30:00Z",
    "testing": {
      "tested": true,
      "test_date": "2025-01-14T15:20:00Z",
      "test_results": "passed",
      "performance_score": 4.8
    },
    "deployment": {
      "environment": "production",
      "deployed_at": "2025-01-15T12:00:00Z",
      "rollback_version": "2.0.0"
    }
  }
}
```

### Key Metadata Fields Explained

- **tags**: Array of labels for quick categorization
- **version**: Semantic version for tracking changes
- **status**: Current lifecycle status (development, testing, production)
- **department**: Owning team or department
- **environment**: Deployment environment
- **testing**: Nested object for test-related metadata
- **deployment**: Nested object for deployment information

### Example Request (curl)

```bash
curl -X 'POST' \
  'https://your-api-endpoint/v1/personas' \
  -H 'accept: application/json' \
  -H 'x-user-id: your-user-id' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Customer Support Agent v2.1",
  "description": "Enhanced customer support persona",
  "content": "You are a helpful and empathetic customer support agent...",
  "metadata": {
    "tags": ["production", "approved"],
    "version": "2.1.0",
    "status": "production",
    "department": "customer_success"
  }
}'
```

### Example Response

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "organization_id": "org-12345",
  "user_id": null,
  "name": "Customer Support Agent v2.1",
  "description": "Enhanced customer support persona",
  "content": "You are a helpful and empathetic customer support agent...",
  "metadata": {
    "tags": ["production", "approved"],
    "version": "2.1.0",
    "status": "production",
    "department": "customer_success"
  },
  "is_active": true,
  "created_at": "2025-01-15T12:00:00Z",
  "updated_at": "2025-01-15T12:00:00Z"
}
```

## Searching and Filtering by Metadata

### API Endpoint

```
GET /v1/personas
```

### Query Parameters

The metadata search system supports flexible querying using dot notation:

#### Simple Field Matching

```bash
# Find personas with specific status
GET /v1/personas?metadata.status=production

# Find personas by department
GET /v1/personas?metadata.department=engineering

# Find personas by version
GET /v1/personas?metadata.version=2.1.0
```

#### Tag-Based Filtering

```bash
# Find personas with specific tag
GET /v1/personas?metadata.tags=approved

# Find personas with multiple tags (OR logic)
GET /v1/personas?metadata.tags=production,approved
```

#### Multiple Criteria (AND Logic)

```bash
# Combine multiple metadata criteria
GET /v1/personas?metadata.status=production&metadata.department=support

# Complex filtering
GET /v1/personas?metadata.tags=approved&metadata.version=2.1.0&metadata.environment=production
```

#### Nested Field Access

```bash
# Query nested metadata fields
GET /v1/personas?metadata.testing.tested=true

# Query deployment environment
GET /v1/personas?metadata.deployment.environment=production
```

### Example Requests

#### Find All Production Personas

```bash
curl -X 'GET' \
  'https://your-api-endpoint/v1/personas?metadata.status=production' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

#### Find Approved Personas in Engineering

```bash
curl -X 'GET' \
  'https://your-api-endpoint/v1/personas?metadata.tags=approved&metadata.department=engineering' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

#### Find Tested Personas

```bash
curl -X 'GET' \
  'https://your-api-endpoint/v1/personas?metadata.testing.tested=true' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

### Example Response

```json
{
  "personas": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Customer Support Agent v2.1",
      "description": "Enhanced customer support persona",
      "metadata": {
        "tags": ["production", "approved"],
        "version": "2.1.0",
        "status": "production",
        "department": "customer_success"
      },
      "is_active": true,
      "created_at": "2025-01-15T12:00:00Z",
      "updated_at": "2025-01-15T12:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

## Updating Persona Metadata

### API Endpoint

```
PUT /v1/personas/{persona_id}
```

### Headers

```
Authorization: Bearer YOUR_JWT_TOKEN
x-user-id: YOUR_USER_ID (if persona is user-restricted)
Content-Type: application/json
```

### Request Body

```json
{
  "name": "Customer Support Agent v2.2",
  "description": "Updated customer support persona",
  "content": "You are a helpful and empathetic customer support agent...",
  "metadata": {
    "tags": ["production", "approved", "updated"],
    "version": "2.2.0",
    "status": "production",
    "department": "customer_success",
    "last_updated": "2025-01-20T14:30:00Z",
    "changelog": [
      {
        "version": "2.2.0",
        "date": "2025-01-20",
        "changes": ["Improved empathy responses", "Added multilingual support"]
      },
      {
        "version": "2.1.0",
        "date": "2025-01-15",
        "changes": ["Enhanced customer support capabilities"]
      }
    ]
  }
}
```

### Example Request (curl)

```bash
curl -X 'PUT' \
  'https://your-api-endpoint/v1/personas/a1b2c3d4-e5f6-7890-abcd-ef1234567890' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "metadata": {
    "tags": ["production", "approved", "updated"],
    "version": "2.2.0",
    "status": "production",
    "last_updated": "2025-01-20T14:30:00Z"
  }
}'
```

## Using Personas with Metadata in Responses API

Personas with metadata work seamlessly with the existing Responses API. The metadata doesn't affect the persona's functionality but provides organizational benefits.

### API Endpoint

```
POST /v1/responses
```

### Request Body

```json
{
  "model": "gpt-4o-mini",
  "input": "I need help with my account",
  "persona_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "max_output_tokens": 150,
  "stream": false
}
```

### Example Request

```bash
curl -X 'POST' \
  'https://your-api-endpoint/v1/responses' \
  -H 'accept: application/json' \
  -H 'x-user-id: customer-123' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "gpt-4o-mini",
  "input": "I need help with my account",
  "persona_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "max_output_tokens": 150,
  "stream": false
}'
```

The response will use the persona's content while the metadata remains available for organizational purposes.

## Analytics Integration

Personas with metadata are fully integrated with the analytics system. You can track usage, performance, and costs for personas organized by their metadata.

### Persona Analytics Endpoint

```
GET /v1/analytics/personas
```

### Filtering Analytics by Metadata

While the analytics API doesn't directly filter by metadata, you can:

1. **Use persona search** to find personas by metadata
2. **Get analytics** for specific personas
3. **Correlate usage** with metadata attributes

### Example Workflow

```bash
# 1. Find all production personas
GET /v1/personas?metadata.status=production

# 2. Get analytics for each production persona
GET /v1/analytics/personas/{persona_id}

# 3. Analyze usage patterns by metadata attributes
```

### Analytics Response

The analytics response includes persona metadata context:

```json
{
  "personas": [
    {
      "persona_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Customer Support Agent v2.1",
      "request_count": 150,
      "success_count": 148,
      "success_rate": 98.7,
      "total_cost": 12.45,
      "last_used_at": "2025-01-20T10:30:00Z"
    }
  ]
}
```

## Use Cases and Examples

### 1. Version Management

Track persona versions and manage deployments:

```json
{
  "metadata": {
    "tags": ["v2", "stable"],
    "version": "2.1.0",
    "status": "production",
    "previous_version": "2.0.0",
    "rollback_available": true,
    "changelog": [
      "Improved response accuracy",
      "Added error handling"
    ]
  }
}
```

### 2. Environment-Based Deployment

Organize personas by deployment environment:

```json
{
  "metadata": {
    "tags": ["development"],
    "environment": "dev",
    "status": "testing",
    "promoted_from": "local",
    "ready_for_staging": false
  }
}
```

### 3. Team Organization

Organize personas by team or department:

```json
{
  "metadata": {
    "tags": ["team-alpha", "customer-support"],
    "department": "customer_success",
    "team": "support-team-alpha",
    "owner": "team-lead@company.com",
    "collaborators": ["dev1@company.com", "dev2@company.com"]
  }
}
```

### 4. A/B Testing

Support experimentation and testing:

```json
{
  "metadata": {
    "tags": ["experiment", "variant-a"],
    "experiment": {
      "name": "support_tone_test",
      "variant": "friendly",
      "start_date": "2025-01-01",
      "end_date": "2025-01-31",
      "traffic_percentage": 50
    }
  }
}
```

### 5. Performance Tracking

Track persona performance and quality:

```json
{
  "metadata": {
    "tags": ["high-performance"],
    "performance": {
      "avg_rating": 4.8,
      "response_time_ms": 1200,
      "success_rate": 0.98,
      "user_satisfaction": 4.7
    },
    "quality_metrics": {
      "accuracy": 0.95,
      "helpfulness": 0.92,
      "clarity": 0.94
    }
  }
}
```

### 6. Integration Metadata

Support external tool integration:

```json
{
  "metadata": {
    "tags": ["integrated"],
    "integrations": {
      "slack": {
        "webhook_url": "https://hooks.slack.com/...",
        "channel": "#support-alerts"
      },
      "jira": {
        "project_key": "SUPPORT",
        "issue_type": "Task"
      }
    }
  }
}
```

## Best Practices

### Metadata Design

1. **Use Consistent Schemas**
   ```json
   {
     "tags": ["array", "of", "strings"],
     "version": "semantic.version.format",
     "status": "enum_value",
     "environment": "enum_value"
   }
   ```

2. **Establish Naming Conventions**
   - Use lowercase with underscores: `last_updated`
   - Use consistent date formats: ISO 8601
   - Use semantic versioning: `major.minor.patch`

3. **Create Metadata Templates**
   ```json
   {
     "tags": [],
     "version": "1.0.0",
     "status": "development",
     "department": "",
     "environment": "dev",
     "testing": {
       "tested": false,
       "test_date": null,
       "test_results": null
     }
   }
   ```

### Organizational Patterns

1. **Lifecycle Management**
   - `development` → `testing` → `staging` → `production`
   - Use status field to track lifecycle stage
   - Use tags for additional context

2. **Version Control**
   - Use semantic versioning
   - Track previous versions for rollback
   - Maintain changelog in metadata

3. **Team Organization**
   - Use department/team fields consistently
   - Track ownership and collaboration
   - Use tags for cross-team personas

### Query Optimization

1. **Index Common Queries**
   - Status-based queries: `metadata.status=production`
   - Department queries: `metadata.department=support`
   - Tag queries: `metadata.tags=approved`

2. **Use Specific Queries**
   ```bash
   # Good: Specific criteria
   ?metadata.status=production&metadata.department=support
   
   # Avoid: Overly broad queries without filters
   ?metadata.tags=*
   ```

3. **Combine with Standard Filters**
   ```bash
   # Combine metadata with standard persona filters
   ?metadata.status=production&is_active=true
   ```

## Troubleshooting

### Common Issues

#### Metadata Not Found in Search

**Problem**: Persona exists but doesn't appear in metadata search results.

**Solutions**:
- Verify the metadata field exists and has the expected value
- Check for typos in field names or values
- Ensure the persona is active (`is_active: true`)

#### Invalid JSON in Metadata

**Problem**: Error when creating or updating persona with metadata.

**Solutions**:
- Validate JSON syntax before sending
- Ensure proper escaping of special characters
- Use consistent data types (strings, numbers, booleans)

#### Search Returns Unexpected Results

**Problem**: Metadata search returns too many or too few results.

**Solutions**:
- Check for case sensitivity in string values
- Verify exact field names (use dot notation correctly)
- Test queries with simpler criteria first

#### Performance Issues with Complex Queries

**Problem**: Slow response times for metadata queries.

**Solutions**:
- Simplify query criteria
- Use more specific filters
- Consider pagination for large result sets
- Contact support for query optimization

### Best Practices for Troubleshooting

1. **Test with Simple Queries First**
   ```bash
   # Start simple
   GET /v1/personas?metadata.status=production
   
   # Then add complexity
   GET /v1/personas?metadata.status=production&metadata.department=support
   ```

2. **Validate Metadata Structure**
   ```bash
   # Get a specific persona to check metadata structure
   GET /v1/personas/{persona_id}
   ```

3. **Use Consistent Data Types**
   ```json
   {
     "version": "2.1.0",        // String
     "tested": true,            // Boolean
     "priority": 1,             // Number
     "tags": ["prod", "test"]   // Array
   }
   ```

### Getting Help

If you encounter issues not covered here:

1. **Check the API Response**: Look for specific error messages
2. **Verify Authentication**: Ensure your JWT token is valid
3. **Test with Simple Cases**: Start with basic metadata queries
4. **Contact Support**: Reach out to support@company.com with:
   - The specific query you're trying to run
   - The expected vs. actual results
   - Any error messages received

---

## Summary

The Persona Metadata system provides powerful organizational capabilities while maintaining full backward compatibility. Use it to:

- **Organize** personas by team, environment, or purpose
- **Version** personas with semantic versioning and changelogs
- **Track** persona lifecycle from development to production
- **Search** personas by any metadata criteria
- **Integrate** with external tools and workflows

The flexible JSON-based approach ensures the system can grow with your organizational needs while providing immediate value for common use cases like versioning and environment management.
