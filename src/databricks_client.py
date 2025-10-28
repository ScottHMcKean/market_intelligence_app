"""Databricks client module for authentication and endpoint calls."""

import json
import os
from typing import Dict, Any, Iterator, Tuple
from databricks.sdk import WorkspaceClient
from mlflow.deployments import get_deploy_client
from openai import OpenAI
import mlflow

from .config import DatabricksConfig


def get_workspace_client() -> WorkspaceClient:
    """Get authenticated Databricks workspace client."""
    return WorkspaceClient()


def get_openai_client(config: DatabricksConfig) -> OpenAI:
    """
    Get OpenAI client configured for Databricks serving endpoints.

    Args:
        config: Databricks configuration

    Returns:
        OpenAI client configured for the Databricks endpoint
    """
    # Get Databricks token from workspace client
    workspace_client = get_workspace_client()
    token = workspace_client.config.token

    # If no token from config, try to get it from databricks CLI
    if not token:
        try:
            import subprocess
            import json as json_module

            result = subprocess.run(
                ["databricks", "auth", "token", "--host", config.host],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # Parse JSON response
                token_data = json_module.loads(result.stdout)
                token = token_data.get("access_token", "")
        except Exception:
            pass

    # Create OpenAI client
    client = OpenAI(api_key=token, base_url=f"{config.host}/serving-endpoints")

    return client


def call_endpoint(
    config: DatabricksConfig,
    question: str,
    max_tokens: int = 10000,
    conversation_history: list = None,
) -> Dict[str, Any]:
    """
    Call the Databricks serving endpoint with a question using OpenAI client.

    Args:
        config: Databricks configuration
        question: User question to send to endpoint
        max_tokens: Maximum tokens for response
        conversation_history: Optional list of previous messages in the conversation

    Returns:
        Dictionary containing the response from the endpoint
    """
    # Get OpenAI client
    client = get_openai_client(config)

    print(f"🔄 Request to: {config.endpoint_name}")
    print(f"📤 Question: {question[:100]}...")
    
    # Build message list with conversation history
    messages = []
    if conversation_history:
        # Add previous messages
        for msg in conversation_history:
            messages.append({"role": "user", "content": msg["question"]})
            if msg.get("answer"):
                messages.append({"role": "assistant", "content": msg["answer"]})
        print(f"📜 Including {len(conversation_history)} previous messages")
    
    # Add current question
    messages.append({"role": "user", "content": question})

    # Make the request
    response = client.responses.create(
        model=config.endpoint_name, 
        input=messages
    )

    print(f"✅ Response received")

    return response


def call_endpoint_stream(
    config: DatabricksConfig,
    question: str,
    max_tokens: int = 10000,
    conversation_history: list = None,
) -> Tuple[Iterator[str], str]:
    """
    Call the Databricks serving endpoint with streaming response using OpenAI client.

    Args:
        config: Databricks configuration
        question: User question to send to endpoint
        max_tokens: Maximum tokens for response
        conversation_history: Optional list of previous messages in the conversation

    Returns:
        Tuple of (text chunk iterator, trace_id)
    """
    # Get the current MLflow span to extract trace_id
    trace_id = None
    
    try:
        # Get OpenAI client
        client = get_openai_client(config)

        print(f"🔄 Streaming request to: {config.endpoint_name}")
        print(f"📤 Question: {question[:100]}...")
        
        # Build message list with conversation history
        messages = []
        if conversation_history:
            # Add previous messages
            for msg in conversation_history:
                messages.append({"role": "user", "content": msg["question"]})
                if msg.get("answer"):
                    messages.append({"role": "assistant", "content": msg["answer"]})
            print(f"📜 Including {len(conversation_history)} previous messages")
        
        # Add current question
        messages.append({"role": "user", "content": question})

        # Make the streaming request
        stream = client.responses.create(
            model=config.endpoint_name,
            input=messages,
            stream=True,
        )
        
        # Generate a simple trace_id for now (can be enhanced later)
        import uuid
        trace_id = str(uuid.uuid4())
        print(f"🔍 Generated trace_id: {trace_id}")

        def stream_generator():
            chunk_count = 0
            full_response = ""
            # Stream the response
            for event in stream:
                chunk_count += 1

                # The event.delta is a string containing the text chunk
                if hasattr(event, "delta") and event.delta:
                    text = event.delta
                    if isinstance(text, str) and text:
                        print(
                            f"📥 Chunk {chunk_count}: {text[:50]}..."
                            if len(text) > 50
                            else f"📥 Chunk {chunk_count}: {text}"
                        )
                        full_response += text
                        yield text

            print(f"✅ Streaming complete: {chunk_count} chunks received")
        
        return stream_generator(), trace_id

    except Exception as e:
        print(f"❌ Streaming error: {e}")
        # If streaming fails, fall back to non-streaming
        import warnings

        warnings.warn(f"Streaming failed: {e}. Falling back to non-streaming.")
        response = call_endpoint(config, question, max_tokens, conversation_history)
        formatted = format_response(response)
        
        def fallback_generator():
            yield formatted
        
        return fallback_generator(), trace_id


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

    # Prepare the request payload (without async flag)
    payload = {
        "input": [{"content": question, "role": "user", "type": "message"}],
    }

    # Make the async request - pass async as a parameter, not in payload
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
        response: Raw response from endpoint (OpenAI response object or dict)

    Returns:
        Formatted response string
    """
    # Handle OpenAI response object from responses.create
    if hasattr(response, "output"):
        # response.output is a list of content items
        output = response.output
        if isinstance(output, list) and len(output) > 0:
            content_item = output[0]
            # Each item has content which is a list
            if hasattr(content_item, "content"):
                content = content_item.content
                if isinstance(content, list) and len(content) > 0:
                    # Get the first content item's text
                    text_item = content[0]
                    if hasattr(text_item, "text"):
                        return str(text_item.text)
                    elif isinstance(text_item, dict) and "text" in text_item:
                        return str(text_item["text"])

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
