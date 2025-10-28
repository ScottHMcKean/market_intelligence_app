"""Tests for configuration module."""

from src.config import DatabricksConfig, DatabaseConfig, AppConfig, OSC_COLORS, OSC_FONTS


def test_databricks_config_from_config():
    """Test DatabricksConfig creation from config file."""
    config = DatabricksConfig.from_config()

    assert config.host is not None
    assert config.endpoint_name is not None
    assert "https://" in config.host


def test_database_config_from_config():
    """Test DatabaseConfig creation from config file."""
    config = DatabaseConfig.from_config()

    # Config from file (no environment variables needed)
    assert config.instance_name is not None
    assert config.database_name == "databricks_postgres"


def test_app_config_from_config():
    """Test AppConfig creation from config file."""
    config = AppConfig.from_config()

    assert config.title is not None
    assert config.layout in ["wide", "centered"]
    assert isinstance(config.async_queries_enabled, bool)


def test_osc_colors():
    """Test OSC color configuration."""
    assert OSC_COLORS["primary"] == "#2e6378"  # OSC Primary Blue
    assert OSC_COLORS["secondary"] == "#2A7DE1"  # Light Blue
    assert OSC_COLORS["accent"] == "#E31837"
    assert OSC_COLORS["background"] == "#F5F5F5"
    assert OSC_COLORS["white"] == "#FFFFFF"
    assert OSC_COLORS["text"] == "#333333"
    assert OSC_COLORS["border"] == "#DDDDDD"


def test_osc_fonts():
    """Test OSC font configuration."""
    assert "Open Sans" in OSC_FONTS["primary"]
    assert "Arial" in OSC_FONTS["secondary"]
