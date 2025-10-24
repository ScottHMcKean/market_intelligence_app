# OSC Market Intelligence App

Streamlit application for market intelligence with Databricks integration, OSC branding, and conversation history management.

## Quick Start

```bash
# Install
uv venv && source .venv/bin/activate
uv pip install -e .

# Configure .env file
DATABRICKS_HOST=https://e2-demo-field-eng.cloud.databricks.com
DATABRICKS_TOKEN=your_token
ENDPOINT_NAME=mas-1ab024e9-endpoint

# Optional: Database for conversation history
DB_HOST=your_lakebase_host
DB_PORT=5432
DB_NAME=market_intelligence
DB_USER=your_user
DB_PASSWORD=your_password

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

Uses Databricks SDK default chain:
1. Environment variables (`DATABRICKS_HOST`, `DATABRICKS_TOKEN`)
2. Configuration profile (`~/.databrickscfg`)
3. OAuth for interactive sessions

Get token: Databricks → User Settings → Developer → Access Tokens

## Troubleshooting

**Authentication errors:** Check token hasn't expired, verify host URL  
**Database issues:** App works without DB, history just won't persist  
**Endpoint errors:** Verify endpoint name and it's running in workspace  

## Deployment

Deploy to Databricks Apps:
1. Package application
2. Upload to workspace
3. Configure secrets for credentials
4. Set environment variables
5. Deploy and share

See: [Databricks Apps documentation](https://docs.databricks.com/apps/index.html)

## Tech Stack

Python 3.10+ • Streamlit • Databricks SDK • PostgreSQL/Lakebase • pytest • uv
