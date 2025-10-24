# Changelog

## [Latest] - Integration Tests Added

### New Features

#### Comprehensive Integration Test Suite
- **Created `tests/test_integration.py`**: Full integration test suite with 16 tests
- **Test Categories**:
  - Databricks authentication and workspace access
  - Database instance validation and credential generation
  - Database connection with WorkspaceClient pattern
  - CRUD operations (conversations, messages)
  - Serving endpoint calls
  - End-to-end workflow validation

#### Helper Scripts
- **`scripts/list_lakebase_instances.py`**: List all available Lakebase instances
  - Shows instance name, state, and host
  - Filters by availability
  - Provides usage examples

#### Test Configuration
- Added `integration` pytest marker for integration tests
- Default test runs skip integration tests (fast unit tests only)
- Separate integration test runs require explicit invocation

### Documentation
- **`tests/INTEGRATION_TESTS.md`**: Comprehensive integration test guide
  - Prerequisites and setup
  - Running tests (all, specific, by marker)
  - Troubleshooting common issues
  - CI/CD integration examples

### Usage

```bash
# Unit tests only (default, fast)
uv run pytest -m "not integration"

# Integration tests (requires live connections)
uv run pytest tests/test_integration.py -v -s

# List available Lakebase instances
uv run python scripts/list_lakebase_instances.py
```

---

## [Updated] - WorkspaceClient Database Integration

### Major Changes

#### Database Configuration Overhaul
- **Removed static credentials**: No more `DB_USER` and `DB_PASSWORD` environment variables needed
- **Implemented WorkspaceClient pattern**: Database credentials are now generated dynamically
- **Enhanced security**: Uses temporary tokens instead of static passwords

#### Configuration Changes

**config.yaml** - Updated database section:
```yaml
database:
  instance_name: "your-lakebase-instance"  # Lakebase instance name
  database_name: "databricks_postgres"     # Database within instance
```

**Old approach (removed)**:
```yaml
database:
  host: "..."
  port: 5432
  name: "..."
  # Plus DB_USER and DB_PASSWORD env vars
```

#### Code Changes

**src/config.py**:
- `DatabaseConfig` now has `instance_name` and `database_name` fields
- Removed `host`, `port`, `user`, `password` fields
- No environment variable dependencies for database config

**src/database.py**:
- `get_connection()` now uses `WorkspaceClient` to generate credentials
- Automatically fetches user email, instance details, and generates tokens
- Connection parameters built dynamically from instance metadata

**app.py**:
- Updated `check_database_connection()` to check `instance_name` instead of `host`
- Removed unused imports (time, check_query_status, update_message, etc.)

**tests/**:
- Updated `test_config.py` to test new `DatabaseConfig` fields
- Updated `test_database.py` fixtures to use new config structure
- All 19 tests passing

#### Benefits

1. **Security**: No static credentials stored anywhere
2. **Simplicity**: Fewer environment variables to manage
3. **Consistency**: Uses same Databricks authentication for everything
4. **Compliance**: Temporary tokens reduce credential exposure
5. **Maintainability**: Single authentication mechanism

### How It Works

```python
# In src/database.py get_connection()
client = WorkspaceClient()  # Uses standard Databricks auth
user = client.current_user.me()
instance = client.database.get_database_instance(name=config.instance_name)
credential = client.database.generate_database_credential(
    request_id=str(uuid.uuid4()),
    instance_names=[config.instance_name]
)

# Connect with temporary credentials
conn = psycopg2.connect(
    host=instance.read_write_dns,
    dbname=config.database_name,
    user=user.emails[0].value,
    password=credential.token,  # Temporary token!
    sslmode="require"
)
```

### Migration Guide

If you were using the old configuration:

1. **Update config.yaml**:
   ```yaml
   database:
     instance_name: "your-lakebase-instance"
     database_name: "databricks_postgres"
   ```

2. **Remove environment variables**:
   ```bash
   # These are no longer needed:
   unset DB_USER
   unset DB_PASSWORD
   ```

3. **Ensure Databricks authentication is configured**:
   - Use `~/.databrickscfg` or
   - Set `DATABRICKS_HOST` and `DATABRICKS_TOKEN` env vars

That's it! The app will now use WorkspaceClient for all database connections.

### Testing

All tests passing:
```bash
$ uv run pytest -v
============================= test session starts ==============================
...
============================== 19 passed in 0.92s ===============================
```

Linting clean:
```bash
$ uv run ruff check src/ app.py tests/
All checks passed!
```

