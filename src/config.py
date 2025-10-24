"""Configuration module for Market Intelligence App."""

import yaml
from dataclasses import dataclass
from pathlib import Path


def load_config_file():
    """Load configuration from config.yaml file."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


CONFIG_DATA = load_config_file()


@dataclass
class DatabricksConfig:
    """Databricks configuration."""

    host: str
    endpoint_name: str

    @classmethod
    def from_config(cls):
        """Create configuration from config.yaml file."""
        db_config = CONFIG_DATA.get("databricks", {})
        host = db_config.get("host", "e2-demo-field-eng.cloud.databricks.com")

        # Add https:// if not present
        if not host.startswith("http"):
            host = f"https://{host}"

        return cls(
            host=host,
            endpoint_name=db_config.get("endpoint_name", "mas-1ab024e9-endpoint"),
        )


@dataclass
class DatabaseConfig:
    """Database configuration for Lakebase.

    Uses Databricks WorkspaceClient to generate credentials dynamically.
    No static credentials needed - authentication via Databricks SDK.
    """

    instance_name: str
    database_name: str
    databricks_host: str  # Workspace host where the instance lives

    @classmethod
    def from_config(cls):
        """
        Create configuration from config.yaml.

        Credentials are generated dynamically via WorkspaceClient,
        so no environment variables needed for database access.
        """
        db_config = CONFIG_DATA.get("database", {})
        databricks_config = CONFIG_DATA.get("databricks", {})

        # Get the databricks host for the database connection
        host = databricks_config.get("host", "")
        if host and not host.startswith("http"):
            host = f"https://{host}"

        return cls(
            instance_name=db_config.get("instance_name", ""),
            database_name=db_config.get("database_name", "databricks_postgres"),
            databricks_host=host,
        )


@dataclass
class AppConfig:
    """Application configuration."""

    title: str
    layout: str
    async_queries_enabled: bool

    @classmethod
    def from_config(cls):
        """Create configuration from config.yaml file."""
        app_config = CONFIG_DATA.get("app", {})

        return cls(
            title=app_config.get("title", "OSC Market Intelligence"),
            layout=app_config.get("layout", "wide"),
            async_queries_enabled=app_config.get("async_queries_enabled", True),
        )


# Ontario Securities Commission Branding
OSC_COLORS = {
    "primary": "#004C97",  # OSC Blue
    "secondary": "#0066CC",  # Light Blue
    "accent": "#FF6B35",  # Accent Orange
    "background": "#F8F9FA",  # Light Gray Background
    "text": "#212529",  # Dark Gray Text
    "white": "#FFFFFF",
}

OSC_FONTS = {
    "primary": "Arial, sans-serif",
    "secondary": "Helvetica, sans-serif",
}
