# Database Queries for Administrators

This document provides a collection of useful SQL queries for administering and monitoring the OpenAI Inference Proxy. These queries can help you troubleshoot issues, analyze usage patterns, and better understand the system's operation.

## How to Use These Queries

You can execute these queries by connecting to your database container:

```bash
docker exec -it openai-inference-proxy-db psql -U proxyuser -d openai_proxy
```

Or run individual queries directly from your host machine:

```bash
docker exec -it openai-inference-proxy-db psql -U proxyuser -d openai_proxy -c "SELECT * FROM organizations;"
```

## Core Entity Queries

### Organizations and API Keys

```sql
-- View all organizations
SELECT * FROM organizations;

-- View API keys (excluding encrypted key for security)
SELECT id, organization_id, synthetic_key, is_active, name, created_at FROM api_keys;
```

### Users and Sessions

```sql
-- View all users
SELECT * FROM users;

-- View all sessions
SELECT * FROM sessions;

-- View session details with first few sessions
SELECT * FROM sessions LIMIT 5;

-- View session requests with ratings
SELECT s.session_id, r.request_id, r.status, r.rating 
FROM sessions s JOIN requests r ON s.id = r.session_id 
ORDER BY s.started_at, r.created_at LIMIT 10;
```

## Request and Usage Analysis

### Basic Request Data

```sql
-- View recent requests (limited)
SELECT * FROM requests LIMIT 5;

-- View recent usage logs (limited)
SELECT * FROM usage_logs LIMIT 5;

-- View recent requests by creation date
SELECT request_id, status, error_message FROM requests ORDER BY created_at DESC;
```

### Request Statistics

```sql
-- Get request status statistics, including rating counts
SELECT 
    status, 
    COUNT(*) as count, 
    COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as with_rating, 
    COUNT(CASE WHEN rating_feedback IS NOT NULL THEN 1 END) as with_feedback 
FROM requests 
GROUP BY status 
ORDER BY count DESC;

-- View recent requests with token usage
SELECT 
    r.request_id, 
    r.status, 
    u.input_tokens, 
    u.output_tokens, 
    u.total_tokens, 
    u.cost_usd 
FROM requests r 
LEFT JOIN usage_logs u ON r.id = u.request_id 
ORDER BY r.created_at DESC 
LIMIT 10;
```

## Troubleshooting Queries

### Failed Requests

```sql
-- View failed requests
SELECT request_id, status, error_message FROM requests WHERE status = 'failed';

-- View failed requests with response payload
SELECT request_id, status, response_payload FROM requests WHERE status = 'failed' LIMIT 3;

-- View failed requests with request payload
SELECT request_id, status, request_payload FROM requests WHERE status = 'failed' LIMIT 3;

-- View failed requests that have ratings
SELECT 
    request_id, 
    status, 
    created_at, 
    completed_at, 
    rating_timestamp 
FROM requests 
WHERE status = 'failed' AND rating IS NOT NULL;
```

### Request Details

```sql
-- Look up a specific request by ID
SELECT request_id, status, error_message 
FROM requests 
WHERE request_id = 'req_fa2515aaba2f4419a6506023ec50d286';

-- View complete request/response data for a specific request
SELECT request_id, status, request_payload, response_payload 
FROM requests 
WHERE request_id = 'req_65f74cfa94a742b793d27e2ea81e244a';
```

## Feedback and Rating Analysis

```sql
-- View all requests with ratings
SELECT request_id, status, rating, rating_feedback 
FROM requests 
WHERE rating IS NOT NULL;

-- View requests with feedback
SELECT request_id, status, rating, rating_feedback 
FROM requests 
WHERE rating_feedback IS NOT NULL;

-- View requests with response_id
SELECT 
    request_id, 
    response_id, 
    rating, 
    rating_feedback, 
    rating_timestamp 
FROM requests 
WHERE response_id IS NOT NULL 
ORDER BY created_at DESC 
LIMIT 5;
```

## Completed Requests

```sql
-- View completed requests with timestamps
SELECT request_id, status, created_at, completed_at 
FROM requests 
WHERE status = 'completed';

-- View completed requests with payloads
SELECT request_id, status, request_payload, response_payload 
FROM requests 
WHERE status = 'completed';
```

## Usage and Cost Analysis

```sql
-- Calculate total tokens and cost by day
SELECT 
    DATE(r.created_at) as date,
    COUNT(r.id) as requests,
    SUM(u.input_tokens) as input_tokens,
    SUM(u.output_tokens) as output_tokens,
    SUM(u.total_tokens) as total_tokens,
    SUM(u.cost_usd) as total_cost
FROM requests r
LEFT JOIN usage_logs u ON r.id = u.request_id
GROUP BY DATE(r.created_at)
ORDER BY date DESC;

-- Calculate tokens and cost by user
SELECT 
    usr.user_id,
    COUNT(r.id) as requests,
    SUM(u.total_tokens) as total_tokens,
    SUM(u.cost_usd) as total_cost
FROM users usr
JOIN sessions s ON usr.id = s.user_id
JOIN requests r ON s.id = r.session_id
LEFT JOIN usage_logs u ON r.id = u.request_id
GROUP BY usr.user_id
ORDER BY total_cost DESC NULLS LAST;
```

## Advanced Performance Analysis

```sql
-- Average response time by status
SELECT 
    status,
    AVG(EXTRACT(EPOCH FROM (completed_at - created_at))) as avg_response_time_seconds,
    COUNT(*) as count
FROM requests
WHERE completed_at IS NOT NULL
GROUP BY status;

-- Requests per hour (last 24 hours)
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as requests
FROM requests
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

These queries should help you monitor and manage your OpenAI Inference Proxy deployment effectively. You can modify them as needed to suit your specific requirements.
