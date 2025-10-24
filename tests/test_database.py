"""Tests for database module."""

import pytest
from unittest.mock import patch, MagicMock
from src.database import (
    create_conversation,
    add_message,
    update_message,
    get_conversation_messages,
    get_message_by_query_id,
    get_user_conversations,
)
from src.config import DatabaseConfig


@pytest.fixture
def db_config():
    """Create a test database configuration."""
    return DatabaseConfig(
        instance_name="test_instance",
        database_name="test_db",
        databricks_host="https://test.cloud.databricks.com",
    )


@pytest.fixture
def mock_connection():
    """Create a mock database connection."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


def test_create_conversation(db_config, mock_connection):
    """Test creating a new conversation."""
    conn, cursor = mock_connection
    cursor.fetchone.return_value = (123,)

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        conversation_id = create_conversation(db_config, "test_user")

        assert conversation_id == 123
        cursor.execute.assert_called_once()
        assert "INSERT INTO conversations" in cursor.execute.call_args[0][0]


def test_add_message(db_config, mock_connection):
    """Test adding a message to a conversation."""
    conn, cursor = mock_connection
    cursor.fetchone.return_value = (456,)

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        message_id = add_message(
            db_config,
            conversation_id=123,
            user_id="test_user",
            question="Test question?",
            answer="Test answer",
            status="complete",
        )

        assert message_id == 456
        cursor.execute.assert_called_once()
        assert "INSERT INTO messages" in cursor.execute.call_args[0][0]


def test_update_message(db_config, mock_connection):
    """Test updating a message."""
    conn, cursor = mock_connection

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        update_message(
            db_config,
            message_id=456,
            answer="Updated answer",
            status="complete",
        )

        cursor.execute.assert_called_once()
        assert "UPDATE messages" in cursor.execute.call_args[0][0]


def test_get_conversation_messages(db_config, mock_connection):
    """Test retrieving conversation messages."""
    conn, cursor = mock_connection
    cursor.fetchall.return_value = [
        {
            "id": 1,
            "question": "Question 1",
            "answer": "Answer 1",
            "status": "complete",
            "query_id": None,
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
        }
    ]

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        messages = get_conversation_messages(db_config, 123)

        assert len(messages) == 1
        assert messages[0]["question"] == "Question 1"


def test_get_message_by_query_id(db_config, mock_connection):
    """Test retrieving a message by query ID."""
    conn, cursor = mock_connection
    cursor.fetchone.return_value = {
        "id": 456,
        "conversation_id": 123,
        "question": "Test question",
        "answer": None,
        "status": "pending",
        "query_id": "query-123",
        "created_at": "2024-01-01",
        "updated_at": "2024-01-01",
    }

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        message = get_message_by_query_id(db_config, "query-123")

        assert message is not None
        assert message["query_id"] == "query-123"
        assert message["status"] == "pending"


def test_get_user_conversations(db_config, mock_connection):
    """Test retrieving user conversations."""
    conn, cursor = mock_connection
    cursor.fetchall.return_value = [
        {
            "id": 123,
            "created_at": "2024-01-01",
            "message_count": 5,
        },
        {
            "id": 124,
            "created_at": "2024-01-02",
            "message_count": 3,
        },
    ]

    with patch("src.database.get_connection") as mock_get_conn:
        mock_get_conn.return_value.__enter__.return_value = conn

        conversations = get_user_conversations(db_config, "test_user")

        assert len(conversations) == 2
        assert conversations[0]["message_count"] == 5
