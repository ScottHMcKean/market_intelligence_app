#!/usr/bin/env python3
"""
Quick test to verify database configuration and connection.

Usage:
    uv run python scripts/test_db_connection.py
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from src.config import DatabaseConfig, DatabricksConfig


def main():
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)

    # Load config
    db_config = DatabaseConfig.from_config()
    databricks_config = DatabricksConfig.from_config()

    print(f"\n📋 Current Configuration:")
    print(f"   Workspace: {databricks_config.host}")
    print(f"   Instance name: {db_config.instance_name}")
    print(f"   Database name: {db_config.database_name}")

    if not db_config.instance_name:
        print("\n❌ No instance_name configured!")
        print("\nTo fix this:")
        print("1. Run: uv run python scripts/list_lakebase_instances.py")
        print("2. Pick an AVAILABLE instance")
        print("3. Update config.yaml with the instance name")
        return

    try:
        # Initialize client
        print("\n🔐 Authenticating with Databricks...")
        client_config = Config(
            host=databricks_config.host,
            auth_type="databricks-cli",  # Use CLI auth to override DEFAULT profile
        )
        client = WorkspaceClient(config=client_config)

        user = client.current_user.me()
        print(f"✅ Authenticated as: {user.emails[0].value}")

        # Check if instance exists
        print(f"\n🔍 Looking for instance '{db_config.instance_name}'...")

        try:
            instance = client.database.get_database_instance(name=db_config.instance_name)
            print(f"✅ Instance found!")
            print(f"   Name: {instance.name}")
            print(f"   State: {instance.state.value}")
            print(f"   Host: {instance.read_write_dns}")

            if instance.state.value != "AVAILABLE":
                print(f"\n⚠️  Warning: Instance is {instance.state.value}, not AVAILABLE")
                print("   The instance needs to be started before you can connect to it.")
                return

        except Exception as e:
            print(f"❌ Instance not found: {e}")
            print(
                f"\nThe instance '{db_config.instance_name}' does not exist or you don't have access."
            )
            print("\nTo find available instances:")
            print("   uv run python scripts/list_lakebase_instances.py")
            return

        # Try to generate credentials
        print(f"\n🔑 Generating database credentials...")
        credential = client.database.generate_database_credential(
            request_id=str(__import__("uuid").uuid4()), instance_names=[db_config.instance_name]
        )
        print(f"✅ Credentials generated (token length: {len(credential.token)} chars)")

        # Try to connect
        print(f"\n🔗 Testing connection to database '{db_config.database_name}'...")
        import psycopg2

        conn = psycopg2.connect(
            host=instance.read_write_dns,
            dbname=db_config.database_name,
            user=user.emails[0].value,
            password=credential.token,
            sslmode="require",
        )

        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Connection successful!")
            print(f"   PostgreSQL version: {version[:50]}...")

        conn.close()

        # Try to initialize tables
        print(f"\n📋 Initializing database schema...")
        from src.database import init_database

        init_database(db_config)
        print(f"✅ Database schema initialized!")
        print(f"   - conversations table created/verified")
        print(f"   - messages table created/verified")
        print(f"   - indexes created/verified")

        print("\n" + "=" * 70)
        print("✅ ALL CHECKS PASSED!")
        print("=" * 70)
        print("\nYour database is properly configured and ready to use.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify the instance name is correct")
        print("2. Ensure the instance is in AVAILABLE state")
        print("3. Check that the database name exists in the instance")
        print("4. Verify you have proper permissions")

        import traceback

        print("\nFull error:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
