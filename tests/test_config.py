"""Tests for configuration module."""
from src.config import DatabricksConfig, DatabaseConfig, OSC_COLORS, OSC_FONTS


def test_databricks_config_from_env(monkeypatch):
    """Test DatabricksConfig creation from environment variables."""
    monkeypatch.setenv("DATABRICKS_HOST", "https://test.databricks.com")
    monkeypatch.setenv("ENDPOINT_NAME", "test-endpoint")
    
    config = DatabricksConfig.from_env()
    
    assert config.host == "https://test.databricks.com"
    assert config.endpoint_name == "test-endpoint"


def test_databricks_config_defaults():
    """Test DatabricksConfig with default values."""
    config = DatabricksConfig.from_env()
    
    assert config.host is not None
    assert config.endpoint_name is not None


def test_database_config_from_env(monkeypatch):
    """Test DatabaseConfig creation from environment variables."""
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "test_db")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_pass")
    
    config = DatabaseConfig.from_env()
    
    assert config.host == "localhost"
    assert config.port == 5433
    assert config.name == "test_db"
    assert config.user == "test_user"
    assert config.password == "test_pass"


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

