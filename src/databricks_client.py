"""Databricks client module for authentication and endpoint calls."""

import json
import os
from typing import Dict, Any
from databricks.sdk import WorkspaceClient
from mlflow.deployments import get_deploy_client

from .config import DatabricksConfig


def get_workspace_client() -> WorkspaceClient:
    """Get authenticated Databricks workspace client."""
    return WorkspaceClient()


def call_endpoint(
    config: DatabricksConfig,
    question: str,
    max_tokens: int = 10000,
) -> Dict[str, Any]:
    """
    Call the Databricks serving endpoint with a question.

    Args:
        config: Databricks configuration
        question: User question to send to endpoint
        max_tokens: Maximum tokens for response

    Returns:
        Dictionary containing the response from the endpoint
    """
    # Set environment variable to force the correct host
    os.environ["DATABRICKS_HOST"] = config.host

    # Get MLflow deployment client
    client = get_deploy_client("databricks")

    # Prepare the request payload
    payload = {
        "inputs": {
            "input": [{"content": question, "role": "user", "type": "message"}],
        }
    }

    # Make the request
    response = client.predict(
        endpoint=config.endpoint_name,
        inputs=payload,
    )

    return response


def call_endpoint_async(
    config: DatabricksConfig,
    question: str,
    max_tokens: int = 10000,
) -> str:
    """
    Call the Databricks serving endpoint asynchronously for long-running queries.

    Args:
        config: Databricks configuration
        question: User question to send to endpoint
        max_tokens: Maximum tokens for response

    Returns:
        Query ID for tracking the async request
    """
    # Set environment variable to force the correct host
    os.environ["DATABRICKS_HOST"] = config.host

    # Get MLflow deployment client
    client = get_deploy_client("databricks")

    # Prepare the request payload with async flag
    payload = {
        "inputs": {
            "input": [{"content": question, "role": "user", "type": "message"}],
        },
        "async": True,
    }

    # Make the async request
    response = client.predict(
        endpoint=config.endpoint_name,
        inputs=payload,
    )

    # Extract query ID from response
    query_id = response.get("query_id") or response.get("id")

    return query_id


def check_query_status(
    config: DatabricksConfig,
    query_id: str,
) -> Dict[str, Any]:
    """
    Check the status of an async query.

    Args:
        config: Databricks configuration
        query_id: The query ID to check

    Returns:
        Dictionary containing query status and results if available
    """
    # Set environment variable to force the correct host
    os.environ["DATABRICKS_HOST"] = config.host

    # Get MLflow deployment client
    client = get_deploy_client("databricks")

    # Note: This might need adjustment based on your endpoint's async API
    # The exact method to check status may vary
    response = client.predict(
        endpoint=config.endpoint_name,
        inputs={"query_id": query_id},
    )

    return response


def get_user_info(client: WorkspaceClient) -> Dict[str, str]:
    """
    Get current user information.

    Args:
        client: Authenticated workspace client

    Returns:
        Dictionary with user information
    """
    current_user = client.current_user.me()

    return {
        "user_id": current_user.user_name or "unknown",
        "display_name": current_user.display_name or current_user.user_name or "User",
        "active": current_user.active,
    }


def format_response(response: Dict[str, Any]) -> str:
    """
    Format the endpoint response for display.

    Args:
        response: Raw response from endpoint

    Returns:
        Formatted response string
    """
    # Handle different response formats
    if "predictions" in response:
        return response["predictions"]
    elif "choices" in response:
        # OpenAI-style response (common for chat endpoints)
        choices = response["choices"]
        if choices and len(choices) > 0:
            message = choices[0].get("message", {})
            return message.get("content", str(response))
        return str(response)
    elif "answer" in response:
        return response["answer"]
    elif "content" in response:
        return response["content"]
    else:
        # Return the full response as JSON string
        return json.dumps(response, indent=2)
