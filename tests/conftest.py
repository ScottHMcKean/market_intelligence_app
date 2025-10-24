"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture(autouse=True)
def reset_env_vars(monkeypatch):
    """Reset environment variables for each test."""
    # Clear any existing test environment variables
    env_vars = [
        "DATABRICKS_HOST",
        "DATABRICKS_TOKEN",
        "ENDPOINT_NAME",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

