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


def format_response(response: Any) -> str:
    """
    Format the endpoint response for display.

    Args:
        response: Raw response from endpoint (could be dict or MLflow response object)

    Returns:
        Formatted response string
    """
    # Handle MLflow DatabricksEndpoint object - it's dict-like
    # Extract the actual response data first
    if hasattr(response, "get"):
        # Try to get predictions key if it exists
        predictions = response.get("predictions")
        if predictions is not None and predictions != response:
            # We got the predictions, use it as the response
            if isinstance(predictions, str):
                # Parse the JSON string
                try:
                    response = json.loads(predictions)
                except (json.JSONDecodeError, TypeError):
                    response = predictions
            elif isinstance(predictions, dict):
                response = predictions
            else:
                response = predictions

    # Convert response to dict if it's not already
    if not isinstance(response, dict):
        # Try to convert to dict if it has a to_dict method or similar
        if hasattr(response, "to_dict"):
            response = response.to_dict()
        elif hasattr(response, "__dict__"):
            response = response.__dict__
        else:
            # Try to access as dict-like object
            try:
                response = dict(response)
            except (TypeError, ValueError):
                return str(response)

    # Handle different response formats

    # Format 1: MLflow deployments format with 'output' list
    if "output" in response:
        output = response.get("output")
        if isinstance(output, list) and len(output) > 0:
            message = output[0]
            # Convert message to dict if needed
            if not isinstance(message, dict):
                if hasattr(message, "__dict__"):
                    message = message.__dict__
                else:
                    try:
                        message = dict(message)
                    except (TypeError, ValueError):
                        pass

            if isinstance(message, dict) and "content" in message:
                content = message.get("content")
                # Handle content list
                if isinstance(content, list) and len(content) > 0:
                    content_item = content[0]
                    # Convert content_item to dict if needed
                    if not isinstance(content_item, dict):
                        if hasattr(content_item, "__dict__"):
                            content_item = content_item.__dict__
                        else:
                            try:
                                content_item = dict(content_item)
                            except (TypeError, ValueError):
                                pass

                    if isinstance(content_item, dict) and "text" in content_item:
                        return str(content_item["text"])
                # Handle direct content string
                elif content:
                    return str(content)

    # Format 2: predictions format (shouldn't reach here after extraction above)
    if "predictions" in response:
        return str(response["predictions"])

    # Format 3: OpenAI-style response (common for chat endpoints)
    if "choices" in response:
        choices = response["choices"]
        if isinstance(choices, list) and len(choices) > 0:
            choice = choices[0]
            if isinstance(choice, dict):
                message = choice.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content")
                    if content:
                        return str(content)

    # Format 4: Simple answer field
    if "answer" in response:
        return str(response["answer"])

    # Format 5: Direct content field
    if "content" in response:
        return str(response["content"])

    # Fallback: Return the full response as JSON string
    return json.dumps(response, indent=2)
