"""
Helper script to create PostgreSQL role for Databricks App service principal.

When a Databricks App connects to Lakebase, it uses its service principal ID
as the database username. This role must exist in PostgreSQL.

Usage:
    uv run python scripts/create_db_role.py <service-principal-uuid>

Example:
    uv run python scripts/create_db_role.py 2ab35418-2e68-42a1-8911-957f8ea7b1a0
"""

import sys
import psycopg2
from psycopg2 import sql
import uuid as uuid_lib

from src.config import DatabaseConfig
from src.database import get_connection


def create_role_for_service_principal(role_uuid: str):
    """
    Create a PostgreSQL role for a Databricks service principal.

    Args:
        role_uuid: The UUID of the service principal (from error message)
    """
    # Validate UUID format
    try:
        uuid_lib.UUID(role_uuid)
    except ValueError:
        print(f"❌ Invalid UUID format: {role_uuid}")
        print(f"   Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        sys.exit(1)

    print(f"Creating PostgreSQL role for service principal: {role_uuid}")
    print("=" * 60)

    # Load database config
    config = DatabaseConfig.from_config()

    try:
        # Connect to database using your current credentials
        print(f"📡 Connecting to database: {config.instance_name}")
        with get_connection(config) as conn:
            with conn.cursor() as cursor:
                # Check if role already exists
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role_uuid,))

                if cursor.fetchone():
                    print(f"⚠️  Role '{role_uuid}' already exists!")
                    print(f"   Updating privileges...")
                else:
                    # Create the role
                    print(f"✓ Creating role '{role_uuid}'...")
                    cursor.execute(
                        sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role_uuid))
                    )

                # Grant privileges
                print(f"✓ Granting CONNECT privilege...")
                cursor.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(config.database_name), sql.Identifier(role_uuid)
                    )
                )

                print(f"✓ Granting USAGE on schema public...")
                cursor.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role_uuid))
                )

                print(f"✓ Granting ALL PRIVILEGES on tables...")
                cursor.execute(
                    sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}").format(
                        sql.Identifier(role_uuid)
                    )
                )

                print(f"✓ Granting ALL PRIVILEGES on sequences...")
                cursor.execute(
                    sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}").format(
                        sql.Identifier(role_uuid)
                    )
                )

                # Grant default privileges for future objects
                print(f"✓ Setting default privileges for future tables...")
                cursor.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT ALL PRIVILEGES ON TABLES TO {}"
                    ).format(sql.Identifier(role_uuid))
                )

                print(f"✓ Setting default privileges for future sequences...")
                cursor.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT ALL PRIVILEGES ON SEQUENCES TO {}"
                    ).format(sql.Identifier(role_uuid))
                )

                # Set security label for OAuth authentication (Lakebase requirement)
                # This maps the OAuth identity (service principal UUID) to the database role
                print(f"✓ Setting OAuth security label...")
                try:
                    cursor.execute(
                        sql.SQL("SECURITY LABEL FOR databricks_iam ON ROLE {} IS %s").format(
                            sql.Identifier(role_uuid)
                        ),
                        (role_uuid,),
                    )
                    print(f"   OAuth identity mapped to role")
                except Exception as label_error:
                    print(f"⚠️  Could not set security label: {label_error}")
                    print(f"   This may be required for OAuth token authentication")
                    print(
                        f"   Try running: SECURITY LABEL FOR databricks_iam ON ROLE \"{role_uuid}\" IS '{role_uuid}';"
                    )

                conn.commit()

                # Verify
                print(f"\n✓ Verifying role...")
                cursor.execute(
                    """
                    SELECT rolname, rolcanlogin, rolconnlimit, rolsuper
                    FROM pg_roles
                    WHERE rolname = %s
                    """,
                    (role_uuid,),
                )

                result = cursor.fetchone()
                if result:
                    rolname, can_login, conn_limit, is_super = result
                    print(f"   Name: {rolname}")
                    print(f"   Can login: {can_login}")
                    print(f"   Connection limit: {conn_limit}")
                    print(f"   Superuser: {is_super}")

                print("\n" + "=" * 60)
                print(f"✅ Role '{role_uuid}' created successfully!")
                print(f"\nYou can now redeploy your Databricks App.")
                print(f"The database connection should work now.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Ensure your current user has admin privileges on the database")
        print(f"2. Verify the Lakebase instance is running")
        print(f"3. Check your config.yaml settings")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("❌ Missing service principal UUID argument")
        print(f"\nUsage:")
        print(f"  python {sys.argv[0]} <service-principal-uuid>")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} 2ab35418-2e68-42a1-8911-957f8ea7b1a0")
        print(f"\nThe UUID is from your error message:")
        print(f'  FATAL: role "2ab35418-2e68-42a1-8911-957f8ea7b1a0" does not exist')
        sys.exit(1)

    role_uuid = sys.argv[1].strip()
    create_role_for_service_principal(role_uuid)


if __name__ == "__main__":
    main()
