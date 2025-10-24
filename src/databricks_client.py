"""Databricks client module for authentication and endpoint calls."""
import json
from typing import Dict, Any
from databricks.sdk import WorkspaceClient

from .config import DatabricksConfig


def get_workspace_client() -> WorkspaceClient:
    """Get authenticated Databricks workspace client."""
    return WorkspaceClient()


def call_endpoint(
    client: WorkspaceClient,
    config: DatabricksConfig,
    question: str,
    max_wait_time: int = 300,
) -> Dict[str, Any]:
    """
    Call the Databricks serving endpoint with a question.
    
    Args:
        client: Authenticated workspace client
        config: Databricks configuration
        question: User question to send to endpoint
        max_wait_time: Maximum time to wait for response in seconds
    
    Returns:
        Dictionary containing the response from the endpoint
    """
    # Prepare the request payload
    payload = {
        "inputs": question,
    }
    
    # Get the API client from workspace client
    api_client = client.api_client
    
    # Make the request
    response = api_client.do(
        method="POST",
        path=f"/serving-endpoints/{config.endpoint_name}/invocations",
        data=payload,
    )
    
    return response


def call_endpoint_async(
    client: WorkspaceClient,
    config: DatabricksConfig,
    question: str,
) -> str:
    """
    Call the Databricks serving endpoint asynchronously for long-running queries.
    
    Args:
        client: Authenticated workspace client
        config: Databricks configuration
        question: User question to send to endpoint
    
    Returns:
        Query ID for tracking the async request
    """
    # Prepare the request payload
    payload = {
        "inputs": question,
        "async": True,  # Request async processing
    }
    
    # Get the API client from workspace client
    api_client = client.api_client
    
    # Make the async request
    response = api_client.do(
        method="POST",
        path=f"/serving-endpoints/{config.endpoint_name}/invocations",
        data=payload,
    )
    
    # Extract query ID from response
    query_id = response.get("query_id") or response.get("id")
    
    return query_id


def check_query_status(
    client: WorkspaceClient,
    config: DatabricksConfig,
    query_id: str,
) -> Dict[str, Any]:
    """
    Check the status of an async query.
    
    Args:
        client: Authenticated workspace client
        config: Databricks configuration
        query_id: The query ID to check
    
    Returns:
        Dictionary containing query status and results if available
    """
    api_client = client.api_client
    
    # Check query status
    response = api_client.do(
        method="GET",
        path=f"/serving-endpoints/{config.endpoint_name}/queries/{query_id}",
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
        # OpenAI-style response
        return response["choices"][0].get("message", {}).get("content", str(response))
    elif "answer" in response:
        return response["answer"]
    else:
        # Return the full response as JSON string
        return json.dumps(response, indent=2)

