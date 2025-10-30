"""Database module for managing conversation history."""

import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
from contextlib import contextmanager
from databricks.sdk import WorkspaceClient

from .config import DatabaseConfig


def init_database(config: DatabaseConfig) -> None:
    """Initialize database schema."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    mlflow_trace_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Add mlflow_trace_id column if it doesn't exist (for existing databases)
            cursor.execute(
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='conversations' AND column_name='mlflow_trace_id'
                    ) THEN
                        ALTER TABLE conversations ADD COLUMN mlflow_trace_id TEXT;
                    END IF;
                END $$;
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT,
                    status TEXT DEFAULT 'pending',
                    query_id TEXT,
                    trace_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
                ON messages(conversation_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_query_id 
                ON messages(query_id)
            """
            )

            conn.commit()


@contextmanager
def get_connection(config: DatabaseConfig):
    """
    Get a database connection using Databricks WorkspaceClient.

    This generates temporary credentials via the Databricks SDK,
    eliminating the need for static database credentials.
    """
    if not config.instance_name:
        raise ValueError("Database instance_name not configured")

    # Initialize WorkspaceClient for the specific workspace
    # Auto-detect authentication method (works locally and in Databricks)
    from databricks.sdk.core import Config as SDKConfig
    import databricks.sdk

    # Check SDK version for debugging
    try:
        sdk_version = getattr(databricks.sdk, "__version__", "unknown")
    except:
        sdk_version = "unknown"

    if config.databricks_host:
        # Create config with explicit host, let SDK auto-detect auth method
        # In Databricks deployment, it will use OAuth with client credentials
        # Locally, it will use CLI auth
        client_config = SDKConfig(host=config.databricks_host)
        client = WorkspaceClient(config=client_config)
    else:
        # Fall back to default config
        client = WorkspaceClient()

    # Verify that the database API is available
    if not hasattr(client, "database"):
        raise AttributeError(
            f"'WorkspaceClient' object has no attribute 'database'. "
            f"This feature requires databricks-sdk>=0.40.0. "
            f"Current SDK version: {sdk_version}. "
            f"Please upgrade: pip install --upgrade 'databricks-sdk>=0.40.0'"
        )

    # Get database instance details
    instance = client.database.get_database_instance(name=config.instance_name)

    # Generate temporary credentials
    # The credential object contains both the username and token
    credential = client.database.generate_database_credential(
        request_id=str(uuid.uuid4()), instance_names=[config.instance_name]
    )

    # Debug: Log credential attributes to help troubleshoot
    print(f"🔍 Credential object type: {type(credential)}")
    print(
        f"🔍 Credential attributes: {[attr for attr in dir(credential) if not attr.startswith('_')]}"
    )

    # Determine the database username
    # For Databricks Apps, the OAuth token is tied to the APP's service principal, not the user
    # We need to find the app's service principal UUID

    db_username = None

    # Option 1: Check environment variables that Databricks Apps might set
    import os

    app_service_principal_id = os.environ.get("DATABRICKS_SERVICE_PRINCIPAL_ID")
    app_client_id = os.environ.get("DATABRICKS_CLIENT_ID")

    print(f"🔍 Environment variables:")
    print(f"   DATABRICKS_SERVICE_PRINCIPAL_ID: {app_service_principal_id}")
    print(f"   DATABRICKS_CLIENT_ID: {app_client_id}")

    if app_service_principal_id:
        db_username = app_service_principal_id
        print(f"✓ Using app service principal ID from environment: {db_username}")
    elif app_client_id:
        db_username = app_client_id
        print(f"✓ Using app client ID from environment: {db_username}")

    # Option 2: Check WorkspaceClient config for OAuth credentials
    if not db_username and hasattr(client, "config"):
        print(
            f"🔍 WorkspaceClient config attributes: {[attr for attr in dir(client.config) if not attr.startswith('_')]}"
        )

        # Check various config fields that might contain the service principal ID
        if hasattr(client.config, "client_id") and client.config.client_id:
            db_username = client.config.client_id
            print(f"✓ Using config.client_id: {db_username}")
        elif hasattr(client.config, "azure_client_id") and client.config.azure_client_id:
            db_username = client.config.azure_client_id
            print(f"✓ Using config.azure_client_id: {db_username}")

    # Option 3: Try to get the service principal that owns this workspace client
    if not db_username:
        try:
            # The current_user.me() returns the END USER, not the app
            # We need the app's identity instead
            user = client.current_user.me()
            print(f"🔍 Current user (end user, not app): {getattr(user, 'user_name', 'N/A')}")
            print(f"🔍 Current user ID: {getattr(user, 'id', 'N/A')}")

            # For now, since we can't reliably get the service principal UUID,
            # we'll use a hardcoded approach or configuration
            # This needs to be the same UUID as in the "role does not exist" error
            print(f"⚠️  Could not automatically determine app service principal UUID")
            print(f"   The OAuth token is for the app's service principal, not the current user")
        except Exception as e:
            print(f"⚠️  Error getting user info: {e}")

    # Option 4: Check if it's set in the database config
    if not db_username and hasattr(config, "service_principal_id") and config.service_principal_id:
        db_username = config.service_principal_id
        print(f"✓ Using service_principal_id from config: {db_username}")

    if not db_username:
        raise ValueError(
            "Could not determine app service principal UUID for database connection. "
            "The OAuth token is issued for the app's service principal, not the current user. "
            "Please set DATABRICKS_SERVICE_PRINCIPAL_ID environment variable or "
            "add service_principal_id to your database config in config.yaml. "
            "Use the UUID from the 'role does not exist' error message."
        )

    # Create connection parameters
    connection_params = {
        "host": instance.read_write_dns,
        "dbname": config.database_name,
        "user": db_username,
        "password": credential.token,
        "sslmode": "require",
    }

    conn = psycopg2.connect(**connection_params)
    try:
        yield conn
    finally:
        conn.close()


def create_conversation(
    config: DatabaseConfig, user_id: str, mlflow_trace_id: Optional[str] = None
) -> int:
    """Create a new conversation."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO conversations (user_id, mlflow_trace_id) VALUES (%s, %s) RETURNING id",
                (user_id, mlflow_trace_id),
            )
            conversation_id = cursor.fetchone()[0]
            conn.commit()
            return conversation_id


def update_conversation_trace(
    config: DatabaseConfig, conversation_id: int, mlflow_trace_id: str
) -> None:
    """Update the MLflow trace ID for a conversation."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE conversations SET mlflow_trace_id = %s WHERE id = %s",
                (mlflow_trace_id, conversation_id),
            )
            conn.commit()


def add_message(
    config: DatabaseConfig,
    conversation_id: int,
    user_id: str,
    question: str,
    answer: Optional[str] = None,
    status: str = "pending",
    query_id: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> int:
    """Add a message to a conversation."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages 
                (conversation_id, user_id, question, answer, status, query_id, trace_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (conversation_id, user_id, question, answer, status, query_id, trace_id),
            )
            message_id = cursor.fetchone()[0]
            conn.commit()
            return message_id


def update_message(
    config: DatabaseConfig,
    message_id: int,
    answer: Optional[str] = None,
    status: Optional[str] = None,
) -> None:
    """Update a message with answer and status."""
    with get_connection(config) as conn:
        with conn.cursor() as cursor:
            updates = []
            params = []

            if answer is not None:
                updates.append("answer = %s")
                params.append(answer)

            if status is not None:
                updates.append("status = %s")
                params.append(status)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(message_id)

                query = f"UPDATE messages SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                conn.commit()


def get_conversation_messages(config: DatabaseConfig, conversation_id: int) -> List[Dict]:
    """Get all messages from a conversation."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, question, answer, status, query_id, created_at, updated_at
                FROM messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            return [dict(row) for row in cursor.fetchall()]


def get_message_by_query_id(config: DatabaseConfig, query_id: str) -> Optional[Dict]:
    """Get a message by query_id for resuming long-running queries."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT id, conversation_id, question, answer, status, query_id, 
                       created_at, updated_at
                FROM messages
                WHERE query_id = %s
                """,
                (query_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None


def get_user_conversations(config: DatabaseConfig, user_id: str) -> List[Dict]:
    """Get all conversations for a user."""
    with get_connection(config) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT c.id, c.created_at, COUNT(m.id) as message_count
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.user_id = %s
                GROUP BY c.id, c.created_at
                ORDER BY c.created_at DESC
                """,
                (user_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
