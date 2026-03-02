# POC 5: Sub-Agent Scoped Credentials

## Overview

This POC implements ephemeral, scoped credentials for sub-agents in Mission Control. Sub-agents are lightweight, temporary entities that can access only specific resources within an organization.

## Key Features

### 1. **Ephemeral API Keys**
- Format: `sk_{sub_agent_id}_{random_secret}`
- Shown **only once** at creation
- 256 bits of entropy in the secret component
- Bcrypt-hashed before storage (only hash is stored)

### 2. **Scoped Access**
Sub-agents can ONLY access:
- Their assigned task (`/orgs/{orgSlug}/tasks/{taskId}`)
- Channels belonging to their task's project (`/orgs/{orgSlug}/channels/{channelId}`)

All other resources return **404** (not 403) to prevent enumeration attacks.

### 3. **Automatic Expiration**
- Configurable timeout (1-168 hours, default 24h)
- Keys are checked on every authentication
- Expired keys are auto-terminated

### 4. **Manual Termination**
- `POST /api/v1/orgs/{orgSlug}/sub-agents/{subAgentId}/terminate`
- Immediately revokes the API key
- Cannot be un-revoked

### 5. **Event Logging**
All sub-agent lifecycle events are logged:
- `sub_agent.created`
- `sub_agent.terminated`

## API Endpoints

### Create Sub-Agent
```http
POST /api/v1/orgs/{orgSlug}/sub-agents
Authorization: Bearer {user_api_key}
Content-Type: application/json

{
  "name": "Task-123-SubAgent",
  "task_id": "660e8400-e29b-41d4-a716-446655440111",
  "timeout_hours": 24
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Task-123-SubAgent",
  "task_id": "660e8400-e29b-41d4-a716-446655440111",
  "project_id": "770e8400-e29b-41d4-a716-446655440222",
  "timeout_at": "2026-02-16T18:00:00Z",
  "api_key": "sk_550e8400-e29b-41d4-a716-446655440000_3x4mpl3s3cr3t"
}
```

⚠️ **Save the `api_key`** - it cannot be retrieved later!

### Get Sub-Agent Info
```http
GET /api/v1/orgs/{orgSlug}/sub-agents/{subAgentId}
Authorization: Bearer {user_api_key}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Task-123-SubAgent",
  "task_id": "660e8400-e29b-41d4-a716-446655440111",
  "project_id": "770e8400-e29b-41d4-a716-446655440222",
  "timeout_at": "2026-02-16T18:00:00Z",
  "terminated": false,
  "terminated_at": null,
  "created_at": "2026-02-15T18:00:00Z"
}
```

### Terminate Sub-Agent
```http
POST /api/v1/orgs/{orgSlug}/sub-agents/{subAgentId}/terminate
Authorization: Bearer {user_api_key}
```

**Response:**
```json
{
  "message": "Sub-agent terminated successfully",
  "terminated_at": "2026-02-15T19:30:00Z"
}
```

## Security Considerations

### 1. **No Enumeration**
- Invalid sub-agent IDs return 404 (not 401)
- Access to out-of-scope resources returns 404 (not 403)
- This prevents attackers from discovering valid resource IDs

### 2. **One-Time Key Display**
- API keys are never stored in plaintext
- They cannot be retrieved after creation
- Lost keys require creating a new sub-agent

### 3. **Bcrypt Hashing**
- Uses bcrypt with automatic salt generation
- Resistant to rainbow table attacks
- Computationally expensive for brute-force

### 4. **Scope Enforcement**
- Checked on **every request**
- Path parameters are validated against sub-agent scope
- List endpoints are denied (sub-agents must know specific IDs)

### 5. **Timeout Enforcement**
- Checked during authentication
- Expired keys are auto-terminated in the database
- No background job needed (lazy enforcement)

## Database Schema

### `sub_agents` Table
```sql
CREATE TABLE sub_agents (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    api_key_hash VARCHAR NOT NULL,
    org_id UUID NOT NULL REFERENCES organizations(id),
    task_id UUID NOT NULL REFERENCES tasks(id),
    project_id UUID NOT NULL REFERENCES projects(id),
    timeout_at TIMESTAMP NOT NULL,
    terminated BOOLEAN DEFAULT FALSE,
    terminated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_sub_agents_org_id ON sub_agents(org_id);
CREATE INDEX ix_sub_agents_task_id ON sub_agents(task_id);
CREATE INDEX ix_sub_agents_project_id ON sub_agents(project_id);
```

## Implementation Details

### Authentication Flow
1. Extract API key from `Authorization` header
2. Check if key starts with `sk_` (sub-agent) or is a UUID (user)
3. For sub-agent keys:
   - Parse format: `sk_{id}_{secret}`
   - Fetch sub-agent by ID and org_id
   - Check if terminated
   - Check if expired (auto-terminate if yes)
   - Verify bcrypt hash
   - Enforce scope on request path

### Scope Verification
```python
async def verify_sub_agent_scope(sub_agent, request, session):
    # Check task_id in path params
    if request.path_params.get("task_id") == sub_agent.task_id:
        return True
    
    # Check channel_id belongs to project
    if channel_id := request.path_params.get("channel_id"):
        channel = await session.get(Channel, channel_id)
        if channel.project_id == sub_agent.project_id:
            return True
    
    # Deny all other access (404)
    raise HTTPException(status_code=404, detail="Resource not found")
```

## Testing

### Manual Testing Steps

1. **Create a user and organization:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/users \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "name": "Test User"}'
   ```

2. **Create a project and task:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orgs/test-org/projects \
     -H "Authorization: Bearer {user_id}" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Project"}'
   
   curl -X POST http://localhost:8000/api/v1/orgs/test-org/tasks \
     -H "Authorization: Bearer {user_id}" \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Task", "project_id": "{project_id}"}'
   ```

3. **Create a sub-agent:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orgs/test-org/sub-agents \
     -H "Authorization: Bearer {user_id}" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test SubAgent", "task_id": "{task_id}", "timeout_hours": 1}'
   ```
   
   **Save the returned `api_key`!**

4. **Test sub-agent access to its task:**
   ```bash
   # Should succeed
   curl http://localhost:8000/api/v1/orgs/test-org/tasks/{task_id} \
     -H "Authorization: Bearer {sub_agent_api_key}"
   ```

5. **Test sub-agent access to other tasks:**
   ```bash
   # Should return 404
   curl http://localhost:8000/api/v1/orgs/test-org/tasks/{other_task_id} \
     -H "Authorization: Bearer {sub_agent_api_key}"
   ```

6. **Terminate the sub-agent:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/orgs/test-org/sub-agents/{sub_agent_id}/terminate \
     -H "Authorization: Bearer {user_id}"
   ```

7. **Test terminated key:**
   ```bash
   # Should return 401
   curl http://localhost:8000/api/v1/orgs/test-org/tasks/{task_id} \
     -H "Authorization: Bearer {sub_agent_api_key}"
   ```

## Future Enhancements

1. **Granular Permissions**
   - Read-only vs. read-write scopes
   - Specific endpoint access lists

2. **Rate Limiting**
   - Per-sub-agent rate limits
   - Prevent abuse of ephemeral credentials

3. **Audit Trail**
   - Log every API call made by sub-agents
   - Track which resources were accessed

4. **Key Rotation**
   - Allow updating timeout without creating new sub-agent
   - Generate new secret while keeping same sub-agent ID

5. **Batch Operations**
   - Create multiple sub-agents at once
   - Bulk termination

## Migration

Run the migration to create the `sub_agents` table:

```bash
cd packages/server
alembic upgrade head
```

## Dependencies

- **bcrypt**: For secure password hashing
- **secrets**: For cryptographically secure random generation
- **FastAPI**: Request context for scope verification
- **SQLModel**: ORM for sub_agents table

## Files Changed/Added

### Added:
- `packages/server/app/models/sub_agent.py`
- `packages/server/app/api/v1/sub_agents.py`
- `packages/server/alembic/versions/b2c3d4e5f6g7_add_sub_agents_table.py`
- `docs/POC5_SUB_AGENTS.md`

### Modified:
- `packages/server/app/models/__init__.py`
- `packages/server/app/api/v1/__init__.py`
- `packages/server/app/core/auth.py`

## License

MIT
