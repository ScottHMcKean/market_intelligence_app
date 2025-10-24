"""Integration tests for Market Intelligence App.

These tests run against live Databricks and Lakebase instances.
They require proper authentication and configuration.

Run with: uv run pytest tests/test_integration.py -v -s
Skip with: uv run pytest -m "not integration"
"""

import pytest
import uuid
from databricks.sdk import WorkspaceClient
from databricks.sdk.errors import NotFound

from src.config import AppConfig, DatabricksConfig, DatabaseConfig
from src.databricks_client import (
    get_workspace_client,
    get_user_info,
    call_endpoint,
    format_response,
)
from src.database import (
    init_database,
    create_conversation,
    add_message,
    update_message,
    get_conversation_messages,
    get_user_conversations,
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def configs():
    """Load configurations once for all tests."""
    return {
        "app": AppConfig.from_config(),
        "databricks": DatabricksConfig.from_config(),
        "database": DatabaseConfig.from_config(),
    }


@pytest.fixture(scope="module")
def workspace_client():
    """Get WorkspaceClient for all tests."""
    try:
        client = get_workspace_client()
        return client
    except Exception as e:
        pytest.skip(f"Could not authenticate with Databricks: {e}")


@pytest.fixture(scope="module")
def user_info(workspace_client):
    """Get current user info."""
    return get_user_info(workspace_client)


@pytest.fixture(scope="module")
def db_available(configs):
    """Check if database is configured and available."""
    db_config = configs["database"]

    if not db_config.instance_name:
        pytest.skip("Database not configured (no instance_name in config.yaml)")

    try:
        client = WorkspaceClient()
        # Try to get the instance
        client.database.get_database_instance(name=db_config.instance_name)
        return True
    except NotFound:
        pytest.skip(f"Database instance '{db_config.instance_name}' not found")
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


class TestDatabricksAuthentication:
    """Test Databricks authentication and workspace access."""

    def test_workspace_client_initialization(self, workspace_client):
        """Test that WorkspaceClient can be initialized."""
        assert workspace_client is not None
        print("\n✅ WorkspaceClient initialized successfully")

    def test_get_current_user(self, workspace_client, user_info):
        """Test that we can get current user information."""
        assert user_info is not None
        assert "user_id" in user_info
        assert "display_name" in user_info
        assert "email" in user_info

        print(f"\n✅ User authenticated:")
        print(f"   User ID: {user_info['user_id']}")
        print(f"   Display Name: {user_info['display_name']}")
        print(f"   Email: {user_info['email']}")

    def test_list_database_instances(self, workspace_client):
        """Test that we can list Lakebase instances."""
        try:
            instances = list(workspace_client.database.list_database_instances())
            assert isinstance(instances, list)

            print(f"\n✅ Found {len(instances)} Lakebase instance(s)")
            if instances:
                print(f"   First instance: {instances[0].name} ({instances[0].state})")
        except Exception as e:
            pytest.fail(f"Could not list database instances: {e}")


class TestDatabaseConnection:
    """Test Lakebase database connection and operations."""

    def test_database_instance_exists(self, configs, workspace_client, db_available):
        """Test that the configured database instance exists."""
        db_config = configs["database"]

        try:
            instance = workspace_client.database.get_database_instance(name=db_config.instance_name)
            assert instance is not None
            assert instance.name == db_config.instance_name

            print(f"\n✅ Database instance found:")
            print(f"   Name: {instance.name}")
            print(f"   State: {instance.state}")
            print(f"   Host: {instance.read_write_dns}")
        except NotFound:
            pytest.fail(f"Database instance '{db_config.instance_name}' not found")

    def test_generate_database_credentials(self, configs, workspace_client, db_available):
        """Test that we can generate temporary database credentials."""
        db_config = configs["database"]

        try:
            credential = workspace_client.database.generate_database_credential(
                request_id=str(uuid.uuid4()), instance_names=[db_config.instance_name]
            )
            assert credential is not None
            assert credential.token is not None

            print(f"\n✅ Generated database credentials:")
            print(f"   Token length: {len(credential.token)} chars")
            print(f"   Temporary token generated successfully")
        except Exception as e:
            pytest.fail(f"Could not generate database credentials: {e}")

    def test_database_connection(self, configs, db_available):
        """Test that we can connect to the database."""
        from src.database import get_connection

        db_config = configs["database"]

        try:
            with get_connection(db_config) as conn:
                assert conn is not None
                # Test a simple query
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    assert result[0] == 1

            print("\n✅ Database connection successful")
            print("   - Connected using WorkspaceClient")
            print("   - Executed test query")
            print("   - Connection closed cleanly")
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

    def test_init_database_schema(self, configs, db_available):
        """Test that we can initialize the database schema."""
        db_config = configs["database"]

        try:
            init_database(db_config)

            print("\n✅ Database schema initialized:")
            print("   - conversations table created/verified")
            print("   - messages table created/verified")
            print("   - indexes created/verified")
        except Exception as e:
            pytest.fail(f"Failed to initialize database schema: {e}")


class TestDatabaseCRUD:
    """Test database CRUD operations."""

    @pytest.fixture(scope="class")
    def test_conversation_id(self, configs, user_info, db_available):
        """Create a test conversation for CRUD tests."""
        db_config = configs["database"]
        conversation_id = create_conversation(db_config, user_info["user_id"])
        print(f"\n✅ Created test conversation ID: {conversation_id}")
        return conversation_id

    def test_create_conversation(self, configs, user_info, db_available):
        """Test creating a new conversation."""
        db_config = configs["database"]

        conversation_id = create_conversation(db_config, user_info["user_id"])
        assert isinstance(conversation_id, int)
        assert conversation_id > 0

        print(f"\n✅ Created conversation ID: {conversation_id}")

    def test_add_message(self, configs, user_info, test_conversation_id, db_available):
        """Test adding a message to a conversation."""
        db_config = configs["database"]

        message_id = add_message(
            db_config,
            conversation_id=test_conversation_id,
            user_id=user_info["user_id"],
            question="Integration test question",
            answer="Integration test answer",
            status="complete",
        )

        assert isinstance(message_id, int)
        assert message_id > 0

        print(f"\n✅ Created message ID: {message_id}")

    def test_add_pending_message(self, configs, user_info, test_conversation_id, db_available):
        """Test adding a pending message with query_id."""
        db_config = configs["database"]

        query_id = f"test-query-{uuid.uuid4()}"
        message_id = add_message(
            db_config,
            conversation_id=test_conversation_id,
            user_id=user_info["user_id"],
            question="Pending test question",
            status="pending",
            query_id=query_id,
        )

        assert isinstance(message_id, int)
        assert message_id > 0

        print(f"\n✅ Created pending message ID: {message_id} (query: {query_id})")
        return message_id, query_id

    def test_update_message(self, configs, user_info, test_conversation_id, db_available):
        """Test updating a message."""
        db_config = configs["database"]

        # Create a pending message
        query_id = f"test-update-{uuid.uuid4()}"
        message_id = add_message(
            db_config,
            conversation_id=test_conversation_id,
            user_id=user_info["user_id"],
            question="Message to update",
            status="pending",
            query_id=query_id,
        )

        # Update it
        update_message(db_config, message_id=message_id, answer="Updated answer", status="complete")

        # Verify update
        messages = get_conversation_messages(db_config, test_conversation_id)
        updated_msg = next(m for m in messages if m["id"] == message_id)

        assert updated_msg["answer"] == "Updated answer"
        assert updated_msg["status"] == "complete"

        print(f"\n✅ Updated message ID: {message_id}")
        print(f"   Status: pending → complete")

    def test_get_conversation_messages(self, configs, test_conversation_id, db_available):
        """Test retrieving conversation messages."""
        db_config = configs["database"]

        messages = get_conversation_messages(db_config, test_conversation_id)

        assert isinstance(messages, list)
        assert len(messages) > 0

        # Verify message structure
        first_msg = messages[0]
        assert "id" in first_msg
        assert "question" in first_msg
        assert "status" in first_msg

        print(f"\n✅ Retrieved {len(messages)} message(s) from conversation {test_conversation_id}")
        print(f"   First message: {first_msg['question'][:50]}...")

    def test_get_user_conversations(self, configs, user_info, db_available):
        """Test retrieving all user conversations."""
        db_config = configs["database"]

        conversations = get_user_conversations(db_config, user_info["user_id"])

        assert isinstance(conversations, list)
        assert len(conversations) > 0

        # Verify conversation structure
        first_conv = conversations[0]
        assert "id" in first_conv
        assert "created_at" in first_conv
        assert "message_count" in first_conv

        print(f"\n✅ Retrieved {len(conversations)} conversation(s)")
        print(
            f"   First conversation: ID {first_conv['id']}, {first_conv['message_count']} message(s)"
        )


class TestDatabricksEndpoint:
    """Test Databricks serving endpoint calls."""

    def test_call_endpoint(self, configs):
        """Test calling the Databricks serving endpoint."""
        databricks_config = configs["databricks"]

        try:
            test_question = "Summarize the Trade execution patterns and suspicious activity rates in the past 24 hours"

            print(f"\n🎯 Calling endpoint: {databricks_config.endpoint_name}")
            print(f"   Question: {test_question}")

            response = call_endpoint(databricks_config, test_question)
            assert response is not None

            # Format and verify response
            answer = format_response(response)
            assert isinstance(answer, str)
            assert len(answer) > 0

            print(f"\n✅ Endpoint call successful")
            print(f"   Response length: {len(answer)} chars")
            print(f"   Answer preview: {answer[:100]}...")

        except Exception as e:
            pytest.fail(f"Endpoint call failed: {e}")

    def test_endpoint_response_format(self, configs):
        """Test that endpoint response can be formatted."""
        databricks_config = configs["databricks"]

        try:
            test_question = "Summarize the Trade execution patterns and suspicious activity rates in the past 24 hours"
            response = call_endpoint(databricks_config, test_question)
            answer = format_response(response)

            assert isinstance(answer, str)
            assert len(answer) > 0
            # Should not contain raw JSON structure
            assert not answer.startswith("{")

            print("\n✅ Response formatted correctly")

        except Exception as e:
            pytest.fail(f"Response formatting failed: {e}")


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_flow(self, configs, user_info, db_available):
        """Test complete flow: create conversation, call endpoint, save result."""
        db_config = configs["database"]
        databricks_config = configs["databricks"]

        print("\n" + "=" * 60)
        print("END-TO-END INTEGRATION TEST")
        print("=" * 60)

        # 1. Create conversation
        print("\n1️⃣ Creating conversation...")
        conversation_id = create_conversation(db_config, user_info["user_id"])
        assert conversation_id > 0
        print(f"   ✅ Conversation ID: {conversation_id}")

        # 2. Call endpoint
        print("\n2️⃣ Calling Databricks endpoint...")
        test_question = "What are key considerations in market intelligence?"
        response = call_endpoint(databricks_config, test_question)
        answer = format_response(response)
        assert len(answer) > 0
        print(f"   ✅ Received answer ({len(answer)} chars)")

        # 3. Save to database
        print("\n3️⃣ Saving to database...")
        message_id = add_message(
            db_config,
            conversation_id=conversation_id,
            user_id=user_info["user_id"],
            question=test_question,
            answer=answer,
            status="complete",
        )
        assert message_id > 0
        print(f"   ✅ Message ID: {message_id}")

        # 4. Retrieve from database
        print("\n4️⃣ Retrieving from database...")
        messages = get_conversation_messages(db_config, conversation_id)
        assert len(messages) > 0

        saved_msg = next(m for m in messages if m["id"] == message_id)
        assert saved_msg["question"] == test_question
        assert saved_msg["answer"] == answer
        assert saved_msg["status"] == "complete"
        print(f"   ✅ Retrieved and verified message")

        print("\n✅ END-TO-END TEST SUCCESSFUL!")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
