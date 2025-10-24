"""Tests for Databricks client module."""

import pytest
from unittest.mock import MagicMock, patch
from src.databricks_client import (
    call_endpoint,
    call_endpoint_async,
    check_query_status,
    get_user_info,
    format_response,
)
from src.config import DatabricksConfig


@pytest.fixture
def databricks_config():
    """Create a test Databricks configuration."""
    return DatabricksConfig(
        host="https://test.databricks.com",
        endpoint_name="test-endpoint",
    )


@pytest.fixture
def mock_workspace_client():
    """Create a mock workspace client."""
    client = MagicMock()
    return client


def test_call_endpoint(databricks_config):
    """Test calling the Databricks endpoint."""
    with patch("src.databricks_client.get_deploy_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.predict.return_value = {"predictions": "Test response"}
        mock_get_client.return_value = mock_client

        response = call_endpoint(
            databricks_config,
            "Test question",
        )

        assert response["predictions"] == "Test response"
        mock_get_client.assert_called_once_with("databricks")
        mock_client.predict.assert_called_once()


def test_call_endpoint_async(databricks_config):
    """Test calling the endpoint asynchronously."""
    with patch("src.databricks_client.get_deploy_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.predict.return_value = {"query_id": "test-query-123"}
        mock_get_client.return_value = mock_client

        query_id = call_endpoint_async(
            databricks_config,
            "Test question",
        )

        assert query_id == "test-query-123"
        mock_get_client.assert_called_once_with("databricks")


def test_check_query_status(databricks_config):
    """Test checking query status."""
    with patch("src.databricks_client.get_deploy_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.predict.return_value = {
            "status": "complete",
            "result": "Test result",
        }
        mock_get_client.return_value = mock_client

        status = check_query_status(
            databricks_config,
            "test-query-123",
        )

        assert status["status"] == "complete"
        assert status["result"] == "Test result"


def test_get_user_info(mock_workspace_client):
    """Test getting user information."""
    mock_user = MagicMock()
    mock_user.user_name = "test@example.com"
    mock_user.display_name = "Test User"
    mock_user.active = True

    mock_workspace_client.current_user.me.return_value = mock_user

    user_info = get_user_info(mock_workspace_client)

    assert user_info["user_id"] == "test@example.com"
    assert user_info["display_name"] == "Test User"
    assert user_info["active"] is True


def test_format_response_predictions():
    """Test formatting response with predictions."""
    response = {"predictions": "Test answer"}
    formatted = format_response(response)
    assert formatted == "Test answer"


def test_format_response_choices():
    """Test formatting response with choices (OpenAI-style)."""
    response = {"choices": [{"message": {"content": "Test answer"}}]}
    formatted = format_response(response)
    assert formatted == "Test answer"


def test_format_response_answer():
    """Test formatting response with answer field."""
    response = {"answer": "Test answer"}
    formatted = format_response(response)
    assert formatted == "Test answer"


def test_format_response_generic():
    """Test formatting generic response."""
    response = {"custom_field": "Custom value"}
    formatted = format_response(response)
    assert "custom_field" in formatted
    assert "Custom value" in formatted
