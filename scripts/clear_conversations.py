"""
Helper script to clear all conversations from the database.

This will delete all conversations and messages, giving you a fresh start.

Usage:
    uv run python scripts/clear_conversations.py
"""

from src.config import DatabaseConfig
from src.database import get_connection


def clear_all_conversations():
    """Delete all conversations and messages from the database."""
    print("Clearing all conversations from the database...")
    print("=" * 60)

    # Load database config
    config = DatabaseConfig.from_config()

    try:
        # Connect to database
        print(f"📡 Connecting to database: {config.instance_name}")
        with get_connection(config) as conn:
            with conn.cursor() as cursor:
                # Count existing data
                cursor.execute("SELECT COUNT(*) FROM messages")
                message_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM conversations")
                conversation_count = cursor.fetchone()[0]

                print(f"\n📊 Current data:")
                print(f"   Conversations: {conversation_count}")
                print(f"   Messages: {message_count}")

                if conversation_count == 0 and message_count == 0:
                    print("\n✓ Database is already empty!")
                    return

                # Delete all messages first (due to foreign key constraints)
                print(f"\n🗑️  Deleting {message_count} messages...")
                cursor.execute("DELETE FROM messages")

                # Delete all conversations
                print(f"🗑️  Deleting {conversation_count} conversations...")
                cursor.execute("DELETE FROM conversations")

                # Reset sequences to start IDs from 1
                print(f"🔄 Resetting ID sequences...")
                cursor.execute("ALTER SEQUENCE conversations_id_seq RESTART WITH 1")
                cursor.execute("ALTER SEQUENCE messages_id_seq RESTART WITH 1")

                conn.commit()

                # Verify
                cursor.execute("SELECT COUNT(*) FROM conversations")
                remaining_conversations = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM messages")
                remaining_messages = cursor.fetchone()[0]

                print("\n" + "=" * 60)
                print(f"✅ Database cleared successfully!")
                print(f"\n📊 After clearing:")
                print(f"   Conversations: {remaining_conversations}")
                print(f"   Messages: {remaining_messages}")
                print(f"\n🎉 Your next conversation will start with ID #1")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Ensure you can connect to the database")
        print(f"2. Verify your Databricks authentication is working")
        print(f"3. Check your config.yaml settings")
        import sys

        sys.exit(1)


if __name__ == "__main__":
    import sys

    print("\n⚠️  WARNING: This will delete ALL conversations and messages!")
    print("This action cannot be undone.\n")

    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() in ["yes", "y"]:
        clear_all_conversations()
    else:
        print("\n❌ Operation cancelled.")
        sys.exit(0)
