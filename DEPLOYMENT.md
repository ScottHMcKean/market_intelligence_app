# Deployment Guide

## Using requirements.txt for Databricks Apps Deployment

### Prerequisites
- Databricks workspace with Apps enabled
- Lakebase instance configured
- Serving endpoint deployed

### Step 1: Verify requirements.txt

The `requirements.txt` file contains all production dependencies:

```
databricks-sdk>=0.40.0  # CRITICAL: Version 0.40.0+ required for Lakebase support
streamlit>=1.30.0
psycopg2-binary>=2.9.9
pyyaml>=6.0.0
mlflow>=2.10.0
openai>=1.0.0
reportlab>=4.0.0
```

**Important:** The `databricks-sdk>=0.40.0` version requirement is critical for Lakebase database support. Earlier versions (like 0.20.0) do not include the `WorkspaceClient.database` API.

### Step 2: Configure config.yaml

Edit `config.yaml` with your deployment settings:

```yaml
databricks:
  host: "https://your-workspace.cloud.databricks.com"  # Your workspace URL
  endpoint_name: "your-endpoint-name"                  # Serving endpoint name

database:
  instance_name: "your-lakebase-instance"              # Lakebase instance name
  database_name: "databricks_postgres"                 # Database name (usually this)
  databricks_host: "https://your-workspace.cloud.databricks.com"  # Same as above
  
  # CRITICAL: Service principal ID for database authentication
  # This is the UUID that appears in the "role does not exist" error
  # Get this from your first deployment attempt error message
  service_principal_id: "2ab35418-2e68-42a1-8911-957f8ea7b1a0"  # Replace with your UUID

app:
  title: "Market Surveillance Analyst"
  layout: "wide"
```

**Important:** The `service_principal_id` is required for Databricks Apps deployments. This UUID must match:
- The role you created in PostgreSQL
- The UUID from the "role does not exist" error message
- The app's service principal identity (not your user ID)

### Step 3: Deploy to Databricks Apps

#### Option A: Using Databricks CLI

```bash
# Navigate to project directory
cd /path/to/market_intelligence_app

# Deploy the app
databricks apps deploy market-intelligence-app \
  --config-file app.yaml \
  --source-dir .

# The deployment will:
# 1. Read requirements.txt automatically
# 2. Install all dependencies in the app environment
# 3. Use app.yaml to determine the start command
# 4. Authenticate using your workspace credentials
```

#### Option B: Using Databricks UI

1. Go to your Databricks workspace
2. Navigate to **Apps** in the left sidebar
3. Click **Create App**
4. Upload your project files:
   - `app.py`
   - `requirements.txt`
   - `app.yaml`
   - `config.yaml`
   - `src/` directory
   - Logo files (`.png`)
5. Databricks will automatically detect `requirements.txt` and install dependencies
6. The app will start using the command from `app.yaml`: `streamlit run app.py`

### Step 4: Verify Deployment

After deployment, verify the app is working:

1. **Check Database Connection:**
   - The app should show conversation history in the sidebar
   - If you see "Database connection not available: 'WorkspaceClient' object has no attribute 'database'", the SDK version is too old

2. **Verify SDK Version:**
   - Check app logs for the error message which now includes version info
   - The error will show the current SDK version and required version

3. **Test Functionality:**
   - Submit a test question
   - Verify conversation history saves
   - Check MLflow tracing

### Troubleshooting

#### "WorkspaceClient has no attribute 'database'"

This error means the databricks-sdk version is too old. Solutions:

1. **Verify requirements.txt:**
   - Ensure it has `databricks-sdk>=0.40.0` (not `>=0.20.0`)
   
2. **Force reinstall in deployment:**
   - If using a cached environment, clear cache and redeploy
   - For Databricks Apps, delete and recreate the app

3. **Test locally first:**
   ```bash
   # Create fresh environment
   python -m venv test_env
   source test_env/bin/activate
   
   # Install from requirements.txt
   pip install -r requirements.txt
   
   # Verify installation
   python test_database_attr.py
   
   # Should show:
   # ✓ WorkspaceClient.database attribute exists
   ```

#### Authentication Issues

The app uses the Databricks SDK authentication chain:

1. **In Databricks Apps (automatic):**
   - Uses the workspace's built-in authentication
   - No configuration needed

2. **For local testing:**
   - Set up `~/.databrickscfg`:
     ```ini
     [DEFAULT]
     host = https://your-workspace.cloud.databricks.com
     token = dapi...
     ```
   - Or use environment variables:
     ```bash
     export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
     export DATABRICKS_TOKEN="dapi..."
     ```

#### Database Connection Issues

If the database connection fails:

1. **"role does not exist" error:**
   ```
   FATAL: role "2ab35418-2e68-42a1-8911-957f8ea7b1a0" does not exist
   ```
   
   This error occurs when the app runs as a service principal but that principal doesn't have a corresponding PostgreSQL role.
   
   **Quick Fix - Use the helper script:**
   ```bash
   # Copy the UUID from your error message
   # Then run:
   uv run python scripts/create_db_role.py 2ab35418-2e68-42a1-8911-957f8ea7b1a0
   ```
   
   **What this does:**
   - Creates the PostgreSQL role with the service principal UUID
   - Grants all necessary privileges
   - Allows the app to connect to the database
   
   **After creating the role:**
   - Redeploy your app or restart it (or just commit changes to database.py to trigger a redeploy)
   - The database connection should work immediately
   - Check the app logs for the debug messages showing successful connection

2. **"no role security label was configured" error:**
   ```
   FATAL: An oauth token was supplied but no role security label was configured
   ```
   
   This error means the role exists but there's a mismatch between the username and OAuth token identity.
   
   **The Fix (already implemented in the code):**
   - The app now uses `user.id` (the service principal UUID) as the database username
   - This matches the OAuth token identity
   - The username must be the same as the UUID in the "role does not exist" error
   - Redeploy the app after updating the code

3. **Verify Lakebase instance:**
   - Instance exists and is running
   - `instance_name` in `config.yaml` matches exactly
   - Your service principal/user has permissions to the Lakebase instance

4. **Graceful degradation:**
   - The app will run without database (no conversation history persistence)
   - Users can still interact with the endpoint, just won't have history

### Local Testing with requirements.txt

Before deploying, test locally:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify databricks-sdk version
python -c "import databricks.sdk; from databricks.sdk import WorkspaceClient; c = WorkspaceClient(); print(f'Has database: {hasattr(c, \"database\")}')"

# Run the app
streamlit run app.py
```

### Environment Variables (Optional)

For additional configuration, you can set these environment variables:

```bash
# Databricks connection
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# MLflow (optional, defaults to databricks://aws)
MLFLOW_TRACKING_URI=databricks://aws
```

### Files Required for Deployment

Minimum required files:
- `app.py` - Main application
- `requirements.txt` - Dependencies
- `app.yaml` - Deployment configuration
- `config.yaml` - App configuration
- `src/` - Source modules
  - `config.py`
  - `database.py`
  - `databricks_client.py`
  - `mlflow_tracing.py`
  - `pdf_generator.py`
- `Ontario_Securities_Commission_logo.svg.png` - OSC logo
- `primary-lockup-full-color-rgb-4000x634.png` - Databricks logo

### Post-Deployment

After successful deployment:

1. **Share the app URL** with users
2. **Monitor usage** via MLflow traces
3. **Check logs** for errors or warnings
4. **Update as needed** by redeploying

### Version Requirements Summary

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| databricks-sdk | **0.40.0** | **Lakebase API support (CRITICAL)** |
| streamlit | 1.30.0 | UI framework |
| psycopg2-binary | 2.9.9 | PostgreSQL connection |
| mlflow | 2.10.0 | Tracing and monitoring |
| openai | 1.0.0 | Endpoint client |

The **databricks-sdk>=0.40.0** requirement is the most critical - earlier versions will cause the "WorkspaceClient has no attribute 'database'" error.

