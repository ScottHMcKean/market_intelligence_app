"""
Helper script to create a static PostgreSQL user for Lakebase database authentication.

This is a workaround for when OAuth token authentication is not available
due to missing databricks_iam security label provider.

Usage:
    uv run python scripts/create_static_db_user.py <username> <password>

Example:
    uv run python scripts/create_static_db_user.py app_user MySecurePassword123
"""

import sys
import psycopg2
from psycopg2 import sql

from src.config import DatabaseConfig
from src.database import get_connection


def create_static_user(username: str, password: str):
    """
    Create a static PostgreSQL user with a password.

    Args:
        username: The PostgreSQL username to create
        password: The password for the user
    """
    print(f"Creating PostgreSQL user: {username}")
    print("=" * 60)

    # Load database config
    config = DatabaseConfig.from_config()

    try:
        # Connect to database using your current credentials (OAuth or existing)
        print(f"📡 Connecting to database: {config.instance_name}")
        with get_connection(config) as conn:
            with conn.cursor() as cursor:
                # Check if user already exists
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))

                if cursor.fetchone():
                    print(f"⚠️  User '{username}' already exists!")
                    print(f"   Updating password...")
                    # Update password
                    cursor.execute(
                        sql.SQL("ALTER ROLE {} WITH PASSWORD %s").format(sql.Identifier(username)),
                        (password,),
                    )
                else:
                    # Create the user
                    print(f"✓ Creating user '{username}'...")
                    cursor.execute(
                        sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s").format(
                            sql.Identifier(username)
                        ),
                        (password,),
                    )

                # Grant privileges
                print(f"✓ Granting CONNECT privilege...")
                cursor.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(config.database_name), sql.Identifier(username)
                    )
                )

                print(f"✓ Granting USAGE on schema public...")
                cursor.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(username))
                )

                print(f"✓ Granting ALL PRIVILEGES on tables...")
                cursor.execute(
                    sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {}").format(
                        sql.Identifier(username)
                    )
                )

                print(f"✓ Granting ALL PRIVILEGES on sequences...")
                cursor.execute(
                    sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {}").format(
                        sql.Identifier(username)
                    )
                )

                # Grant default privileges for future objects
                print(f"✓ Setting default privileges for future tables...")
                cursor.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT ALL PRIVILEGES ON TABLES TO {}"
                    ).format(sql.Identifier(username))
                )

                print(f"✓ Setting default privileges for future sequences...")
                cursor.execute(
                    sql.SQL(
                        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
                        "GRANT ALL PRIVILEGES ON SEQUENCES TO {}"
                    ).format(sql.Identifier(username))
                )

                conn.commit()

                # Verify
                print(f"\n✓ Verifying user...")
                cursor.execute(
                    """
                    SELECT rolname, rolcanlogin, rolconnlimit, rolsuper
                    FROM pg_roles
                    WHERE rolname = %s
                    """,
                    (username,),
                )

                result = cursor.fetchone()
                if result:
                    rolname, can_login, conn_limit, is_super = result
                    print(f"   Name: {rolname}")
                    print(f"   Can login: {can_login}")
                    print(f"   Connection limit: {conn_limit}")
                    print(f"   Superuser: {is_super}")

                print("\n" + "=" * 60)
                print(f"✅ User '{username}' created successfully!")
                print(f"\nNext steps:")
                print(f"1. Set these environment variables in your Databricks App:")
                print(f"   LAKEBASE_DB_USER={username}")
                print(f"   LAKEBASE_DB_PASSWORD={password}")
                print(f"\n2. Redeploy your app")
                print(f"\n3. The app will automatically use these static credentials")
                print(f"   when OAuth token authentication is not available")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Ensure your current user has admin privileges on the database")
        print(f"2. Verify the Lakebase instance is running")
        print(f"3. Check your config.yaml settings")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("❌ Missing username and password arguments")
        print(f"\nUsage:")
        print(f"  python {sys.argv[0]} <username> <password>")
        print(f"\nExample:")
        print(f"  python {sys.argv[0]} app_user MySecurePassword123")
        print(f"\nThis creates a PostgreSQL user with static credentials")
        print(f"for use when OAuth token authentication is not available.")
        sys.exit(1)

    username = sys.argv[1].strip()
    password = sys.argv[2].strip()

    if not username or not password:
        print("❌ Username and password cannot be empty")
        sys.exit(1)

    if len(password) < 8:
        print("⚠️  Warning: Password is very short. Consider using a stronger password.")

    create_static_user(username, password)


if __name__ == "__main__":
    main()
