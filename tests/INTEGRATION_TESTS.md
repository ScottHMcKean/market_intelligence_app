# Integration Tests

Integration tests that validate the application against live Databricks and Lakebase instances.

## Overview

These tests verify:
- ✅ Databricks authentication and workspace access
- ✅ Lakebase instance availability and credentials
- ✅ Database connection with WorkspaceClient pattern
- ✅ Database schema initialization
- ✅ CRUD operations (create, read, update)
- ✅ Databricks serving endpoint calls
- ✅ End-to-end flow (conversation → endpoint → database)

## Prerequisites

### 1. Databricks Authentication

Configure Databricks authentication using one of:

**Option A: Configuration file (recommended)**
```bash
# Create ~/.databrickscfg
cat > ~/.databrickscfg << EOF
[DEFAULT]
host = https://your-workspace.cloud.databricks.com
token = your-token-here
EOF
```

**Option B: Environment variables**
```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=your-token-here
```

### 2. Configuration File

Ensure `config.yaml` is properly configured:

```yaml
databricks:
  host: "your-workspace.cloud.databricks.com"
  endpoint_name: "your-endpoint-name"

database:
  instance_name: "your-lakebase-instance"
  database_name: "databricks_postgres"
```

### 3. Lakebase Instance

The database instance must:
- Exist and be in `AVAILABLE` state
- Be accessible by your Databricks user
- Have the specified database created

**List available instances:**
```python
from databricks.sdk import WorkspaceClient
client = WorkspaceClient()
for instance in client.database.list_database_instances():
    print(f"{instance.name}: {instance.state}")
```

## Running Integration Tests

### Run all integration tests
```bash
uv run pytest tests/test_integration.py -v -s
```

### Run specific test class
```bash
# Test only database operations
uv run pytest tests/test_integration.py::TestDatabaseCRUD -v -s

# Test only endpoint calls
uv run pytest tests/test_integration.py::TestDatabricksEndpoint -v -s
```

### Run specific test
```bash
uv run pytest tests/test_integration.py::TestDatabaseConnection::test_database_connection -v -s
```

### Run with markers
```bash
# Run all tests including integration
uv run pytest tests/ -v -s

# Run only unit tests (skip integration)
uv run pytest tests/ -v -m "not integration"

# Run only integration tests
uv run pytest tests/ -v -m integration
```

## Test Structure

### `TestDatabricksAuthentication`
- `test_workspace_client_initialization` - Verify client setup
- `test_get_current_user` - Get authenticated user info
- `test_list_database_instances` - List available Lakebase instances

### `TestDatabaseConnection`
- `test_database_instance_exists` - Verify configured instance exists
- `test_generate_database_credentials` - Generate temporary tokens
- `test_database_connection` - Test connection with WorkspaceClient
- `test_init_database_schema` - Initialize tables and indexes

### `TestDatabaseCRUD`
- `test_create_conversation` - Create new conversation
- `test_add_message` - Add message to conversation
- `test_add_pending_message` - Add pending message with query_id
- `test_update_message` - Update message status and answer
- `test_get_conversation_messages` - Retrieve conversation history
- `test_get_user_conversations` - List user's conversations

### `TestDatabricksEndpoint`
- `test_call_endpoint` - Call serving endpoint
- `test_endpoint_response_format` - Verify response formatting

### `TestEndToEnd`
- `test_complete_flow` - Full workflow test

## Troubleshooting

### Authentication Error
```
Could not authenticate with Databricks: ...
```
**Solution:** Check `~/.databrickscfg` or `DATABRICKS_HOST`/`DATABRICKS_TOKEN` env vars

### Instance Not Found
```
Database instance 'xxx' not found
```
**Solution:** 
1. List available instances (see Prerequisites #3)
2. Update `instance_name` in `config.yaml`

### Endpoint Error
```
Endpoint call failed: ...
```
**Solution:**
1. Verify endpoint exists: Check Databricks workspace → Serving
2. Verify endpoint is running
3. Update `endpoint_name` in `config.yaml`

### Connection Timeout
```
Database connection failed: timeout
```
**Solution:**
- Check instance state (should be `AVAILABLE`)
- Verify network connectivity
- Check workspace firewall rules

## Test Data

Integration tests create real data:
- Conversations in the database
- Messages with test content
- These can be cleaned up manually if needed

Test messages are clearly labeled:
- "Integration test question"
- "Test question"
- Query IDs start with "test-"

## CI/CD Integration

**Skip integration tests in CI:**
```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: uv run pytest -m "not integration"
```

**Run integration tests on schedule:**
```yaml
# .github/workflows/integration.yml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
jobs:
  test:
    steps:
      - name: Run integration tests
        run: uv run pytest tests/test_integration.py -v
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

## Development

When adding new integration tests:

1. **Mark as integration:**
   ```python
   @pytest.mark.integration
   def test_new_feature():
       ...
   ```

2. **Use fixtures:**
   - `configs` - Load configurations
   - `workspace_client` - Databricks client
   - `user_info` - Current user info
   - `db_available` - Skip if DB not available

3. **Handle failures gracefully:**
   ```python
   def test_something(db_available):
       # db_available will skip if DB not configured
       ...
   ```

4. **Print progress:**
   ```python
   print("\n✅ Test passed")
   print(f"   Detail: {value}")
   ```

## Quick Reference

```bash
# Run all tests (unit only by default)
uv run pytest

# Include integration tests
uv run pytest tests/test_integration.py -v -s

# End-to-end test only
uv run pytest tests/test_integration.py::TestEndToEnd -v -s

# Check what instances are available
uv run python -c "from databricks.sdk import WorkspaceClient; [print(f'{i.name}: {i.state}') for i in WorkspaceClient().database.list_database_instances()]"
```

