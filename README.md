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

# Set database credentials as environment variables (optional)
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password

# Databricks authentication uses SDK defaults (~/.databrickscfg or environment)
# See: https://docs.databricks.com/dev-tools/auth.html

# Run
uv run streamlit run app.py
```

## Features

- 🔐 Databricks Workspace Client authentication
- 💬 Conversation history (Lakebase/PostgreSQL)
- ⚡ Async query support for long-running operations
- 🎨 OSC branding (Primary: #004C97, Secondary: #0066CC)
- 📊 AI-powered market intelligence via Databricks endpoints

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
uv run pytest                    # Run tests
uv run pytest --cov=src          # With coverage
uv run jupyter notebook test_components.ipynb  # Interactive
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

**Database:** Credentials from environment only
- `DB_USER` and `DB_PASSWORD` environment variables
- Or Databricks secrets in production

Get Databricks token: Workspace → User Settings → Developer → Access Tokens

## Troubleshooting

**Authentication errors:** Check `~/.databrickscfg` exists or set `DATABRICKS_HOST`/`DATABRICKS_TOKEN` env vars  
**Database issues:** App works without DB, history just won't persist. Check `DB_USER`/`DB_PASSWORD` env vars  
**Endpoint errors:** Verify endpoint name in `config.yaml` and it's running in workspace  

## Deployment

Deploy to Databricks Apps:
1. Package application
2. Upload to workspace
3. Configure secrets for credentials
4. Set environment variables
5. Deploy and share

See: [Databricks Apps documentation](https://docs.databricks.com/apps/index.html)

## Tech Stack

Python 3.10+ • Streamlit • Databricks SDK • MLflow • PostgreSQL/Lakebase • pytest • uv
