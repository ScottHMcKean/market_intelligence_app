"""Configuration module for Market Intelligence App."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabricksConfig:
    """Databricks configuration."""
    
    host: str
    endpoint_name: str
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("DATABRICKS_HOST", "https://e2-demo-field-eng.cloud.databricks.com"),
            endpoint_name=os.getenv("ENDPOINT_NAME", "mas-1ab024e9-endpoint"),
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
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", ""),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "market_intelligence"),
            user=os.getenv("DB_USER", ""),
            password=os.getenv("DB_PASSWORD", ""),
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

