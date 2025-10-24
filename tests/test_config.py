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
    assert OSC_COLORS["primary"] == "#004C97"
    assert OSC_COLORS["secondary"] == "#0066CC"
    assert OSC_COLORS["accent"] == "#FF6B35"
    assert OSC_COLORS["background"] == "#F8F9FA"
    assert OSC_COLORS["text"] == "#212529"
    assert OSC_COLORS["white"] == "#FFFFFF"


def test_osc_fonts():
    """Test OSC font configuration."""
    assert "Arial" in OSC_FONTS["primary"]
    assert "Helvetica" in OSC_FONTS["secondary"]
