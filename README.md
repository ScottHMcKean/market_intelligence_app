# OSC Market Intelligence App

Streamlit application for market intelligence with Databricks integration, OSC branding, and conversation history management.

## Quick Start

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e .

# Edit config.yaml with your settings (no credentials!)
databricks:
  host: "e2-demo-field-eng.cloud.databricks.com"
  endpoint_name: "mas-1ab024e9-endpoint"

database:
  instance_name: "your-lakebase-instance"
  database_name: "databricks_postgres"

# Databricks authentication uses SDK defaults (~/.databrickscfg or environment)
# Database credentials are generated dynamically - no env vars needed!
# See: https://docs.databricks.com/dev-tools/auth.html

# Run
uv run streamlit run app.py
```

## Features

- 🔐 Databricks Workspace Client authentication
- 👤 Personalized user welcome and authentication
- 💬 Conversation history with sidebar navigation (Lakebase/PostgreSQL with dynamic credentials)
- 📜 Browse past conversations by user
- ⚡ Async query support for long-running operations
- 🎨 OSC branding with official colors (Primary: #003DA5, from https://www.osc.ca/en)
- 🖼️ OSC logo integration
- 📊 AI-powered market intelligence via Databricks endpoints
- 🎯 Modern, responsive UI with Open Sans font

## Architecture

```
src/
├── config.py              # Configuration with OSC branding
├── database.py            # Conversation history (Lakebase)
├── databricks_client.py   # Endpoint calls & auth
app.py                     # Main Streamlit app
config.yaml                # Non-sensitive configuration
test_components.ipynb      # Interactive testing
tests/                     # Unit tests (19 tests, 100% pass)
```

## Development

**Testing:**
```bash
uv pip install -e ".[dev]"

# Unit tests only (fast, no live connections)
uv run pytest -m "not integration"

# All tests including integration (requires live connections)
uv run pytest tests/test_integration.py -v -s

# With coverage
uv run pytest --cov=src -m "not integration"

# Interactive testing
uv run jupyter notebook test_components.ipynb
```

**Integration Tests:**

Integration tests validate against live Databricks and Lakebase instances.
See [tests/INTEGRATION_TESTS.md](tests/INTEGRATION_TESTS.md) for details.

```bash
# Run all integration tests
uv run pytest tests/test_integration.py -v -s

# Run specific test
uv run pytest tests/test_integration.py::TestEndToEnd -v -s
```

**Code Quality:**
```bash
uv run black src tests           # Format
uv run ruff check src tests      # Lint
```

## Design Principles

- Simple, modular functions with single responsibilities
- Functions over classes, composition over inheritance
- Clear dependencies for testability
- Databricks-ready for production deployment
- Graceful degradation (works without database)

## Authentication

**Databricks:** Uses SDK default chain (no credentials in config files)
1. Configuration profile (`~/.databrickscfg`) - recommended
2. Environment variables (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`)
3. OAuth for interactive sessions

**Database (Lakebase):** Uses WorkspaceClient for dynamic credential generation
- No static credentials needed!
- Credentials generated automatically via `client.database.generate_database_credential()`
- Uses current user's Databricks authentication
- Temporary tokens for enhanced security

Get Databricks token: Workspace → User Settings → Developer → Access Tokens

## Troubleshooting

**Authentication errors:** Check `~/.databrickscfg` exists or set `DATABRICKS_HOST`/`DATABRICKS_TOKEN` env vars  
**Database issues:** App works without DB, history just won't persist. Verify `instance_name` in `config.yaml`  
**Endpoint errors:** Verify endpoint name in `config.yaml` and it's running in workspace  
**"WorkspaceClient has no attribute 'database'":** This indicates an outdated databricks-sdk version
- Required: `databricks-sdk>=0.40.0` (for Lakebase support)
- Check your version: `uv run python -c "from databricks.sdk import WorkspaceClient; c = WorkspaceClient(); print(hasattr(c, 'database'))"`
- Should print `True` if installed correctly
- If running without `uv run`, ensure you're using the correct Python environment with the updated SDK
- Run test: `uv run python test_database_attr.py` to verify installation  

## Deployment

Deploy to Databricks Apps using `requirements.txt`. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete deployment guide.

**Quick deployment:**
```bash
databricks apps deploy market-intelligence-app \
  --config-file app.yaml \
  --source-dir .
```

**Key requirements:**
- `databricks-sdk>=0.40.0` (for Lakebase support)
- Configured `config.yaml` with your workspace details
- Lakebase instance running
- Serving endpoint deployed

See: [Databricks Apps documentation](https://docs.databricks.com/apps/index.html)

## Tech Stack

Python 3.10+ • Streamlit • Databricks SDK • MLflow • PostgreSQL/Lakebase • pytest • uv
