#!/usr/bin/env python3
"""
List available Lakebase instances in the current Databricks workspace.

Usage:
    uv run python scripts/list_lakebase_instances.py
"""

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from src.config import DatabricksConfig


def main():
    print("=" * 70)
    print("LAKEBASE INSTANCES IN CURRENT WORKSPACE")
    print("=" * 70)

    try:
        # Load the configured Databricks workspace
        databricks_config = DatabricksConfig.from_config()

        print(f"\n🎯 Target Workspace: {databricks_config.host}")

        # Initialize client with the configured workspace
        # Explicitly set auth_type to override .databrickscfg DEFAULT profile
        client_config = Config(host=databricks_config.host, auth_type="databricks-cli")
        client = WorkspaceClient(config=client_config)

        # Get current user
        user = client.current_user.me()
        print(f"\n👤 Authenticated as: {user.emails[0].value}")
        print(f"   Workspace: {client.config.host}")

        # List instances
        print("\n📊 Fetching instances...")
        instances = list(client.database.list_database_instances())

        if not instances:
            print("\n⚠️  No Lakebase instances found")
            print("\nPossible reasons:")
            print("  - No instances provisioned yet")
            print("  - Insufficient permissions to list instances")
            print("  - Wrong workspace")
            return

        # Filter to available instances
        available = [i for i in instances if i.state.value == "AVAILABLE"]
        stopped = [i for i in instances if i.state.value == "STOPPED"]
        other = [i for i in instances if i.state.value not in ["AVAILABLE", "STOPPED"]]

        print(f"\n✅ Found {len(instances)} instance(s):")
        print(f"   - {len(available)} AVAILABLE")
        print(f"   - {len(stopped)} STOPPED")
        print(f"   - {len(other)} Other states")

        # Show available instances (recommended for use)
        if available:
            print("\n" + "=" * 70)
            print("AVAILABLE INSTANCES (recommended)")
            print("=" * 70)
            for instance in sorted(available, key=lambda x: x.name):
                print(f"\n📦 {instance.name}")
                print(f"   State: {instance.state.value}")
                print(f"   Host: {instance.read_write_dns}")
                if hasattr(instance, "size"):
                    print(f"   Size: {instance.size}")

        # Show stopped instances
        if stopped:
            print("\n" + "=" * 70)
            print("STOPPED INSTANCES (need to be started)")
            print("=" * 70)
            for instance in sorted(stopped, key=lambda x: x.name):
                print(f"\n⏸️  {instance.name}")
                print(f"   State: {instance.state.value}")

        # Show other states
        if other:
            print("\n" + "=" * 70)
            print("OTHER STATES")
            print("=" * 70)
            for instance in sorted(other, key=lambda x: x.name):
                print(f"\n🔄 {instance.name}")
                print(f"   State: {instance.state.value}")

        # Instructions
        print("\n" + "=" * 70)
        print("USAGE")
        print("=" * 70)
        print("\nTo use an instance, update config.yaml:")
        print("\n  database:")
        print('    instance_name: "<instance-name>"')
        print('    database_name: "databricks_postgres"')

        if available:
            print(f"\nExample with first available instance:")
            print(f"\n  database:")
            print(f'    instance_name: "{available[0].name}"')
            print(f'    database_name: "databricks_postgres"')

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Databricks authentication (~/.databrickscfg)")
        print("  2. Verify DATABRICKS_HOST and DATABRICKS_TOKEN env vars")
        print("  3. Ensure you have permissions to list database instances")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
