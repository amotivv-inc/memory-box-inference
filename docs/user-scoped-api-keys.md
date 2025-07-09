# User-Scoped API Keys Implementation

## Overview

This document describes the implementation of user-scoped API key validation in the Enterprise AI Gateway, which provides fine-grained access control for audit purposes.

## Implementation Details

### 1. Database Schema

API keys have an optional `user_id` field that creates two scoping models:

- **Organization-Scoped Keys** (`user_id = NULL`): Shared across the entire organization
- **User-Scoped Keys** (`user_id = specific user`): Restricted to a specific user

### 2. Key Resolution Logic

The `KeyMapperService.get_api_key_for_request()` method implements a priority-based lookup:

1. First, check for a user-specific API key
2. If not found, fall back to organization-wide API key
3. If neither exists, deny access

```python
async def get_api_key_for_request(
    self, 
    organization_id: str, 
    user_id: str
) -> Optional[APIKey]:
    # Try user-specific key first
    user_key = await self._find_user_key(organization_id, user_id)
    if user_key:
        return user_key
    
    # Fall back to org-wide key
    return await self._find_org_key(organization_id)
```

### 3. Request Flow

1. JWT token identifies the organization
2. X-User-ID header identifies the user
3. System finds or creates the user record
4. Appropriate API key is selected based on user/org
5. Request is forwarded to AI provider with the decrypted key

### 4. Audit Benefits

- **User-Level Access Control**: Different users can have different AI provider keys
- **Usage Tracking**: All requests are tied to specific users and API keys
- **Granular Permissions**: Revoke access for specific users without affecting others
- **Compliance**: Complete audit trail of who used which API key when

## Testing

### Development Test Script
For detailed testing during development:

```bash
./dev-scripts/test_user_scoped_keys.sh
```

This tests:
- User-specific API key access
- Fallback to organization-wide keys
- Key deactivation
- Organization isolation
- Error handling

### Comprehensive Test Suite
For full API testing including user-scoped keys:

```bash
python tests/openai_proxy_test.py
```

This includes all user-scoped API key tests as part of the complete test suite.

## Usage Examples

### Create a User-Specific API Key

```bash
# Create user
docker exec openai-proxy-api python scripts/manage_users.py create-user $ORG_ID "alice"

# Create API key for user
docker exec openai-proxy-api python scripts/manage_api_keys.py create-key $ORG_ID $AI_PROVIDER_KEY \
  --user-id $USER_ID \
  --name "Alice's Personal Key"
```

### Create an Organization-Wide API Key

```bash
# Create API key without user association
docker exec openai-proxy-api python scripts/manage_api_keys.py create-key $ORG_ID $AI_PROVIDER_KEY \
  --name "Shared Organization Key"
```

## API Endpoints

The implementation doesn't require any new API endpoints. The existing `/v1/responses` endpoint now automatically handles user-scoped validation based on:

- JWT token (organization identification)
- X-User-ID header (user identification)
- API key associations in the database

## Security Considerations

1. **Automatic User Creation**: Users are created on-demand if they don't exist
2. **Key Priority**: User-specific keys always take precedence over org-wide keys
3. **Deactivation**: Deactivated keys are immediately rejected
4. **Organization Isolation**: Keys from one organization cannot be used by another

## Future Enhancements

1. **Rate Limiting**: Apply different rate limits to different users
2. **Model Restrictions**: Limit certain users to specific AI models
3. **Usage Quotas**: Set per-user usage limits
4. **Key Rotation**: Automated key rotation policies per user
