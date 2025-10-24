"""Configuration module for Market Intelligence App."""

import os
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
    """Database configuration for Lakebase."""

    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_config(cls):
        """
        Create configuration from config.yaml and environment variables.

        Sensitive credentials (user, password) come from environment variables only.
        Non-sensitive settings come from config.yaml.
        """
        db_config = CONFIG_DATA.get("database", {})

        return cls(
            host=db_config.get("host", ""),
            port=db_config.get("port", 5432),
            name=db_config.get("name", "market_intelligence"),
            # Credentials come from environment only (or Databricks secrets)
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
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
