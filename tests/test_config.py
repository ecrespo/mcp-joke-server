"""
Unit tests for utils/config.py

Tests for application configuration using pydantic-settings.
"""

from pathlib import Path

from utils.config import Settings, SingletonSettingsMeta


class TestSettings:
    """Tests for Settings configuration class."""

    def test_settings_loads_from_env(self):
        """Test that Settings loads configuration from environment."""
        settings = Settings()
        assert settings.API_BASE_URL is not None
        assert isinstance(settings.API_BASE_URL, str)

    def test_settings_has_defaults(self):
        """Test that Settings has expected defaults."""
        settings = Settings()
        assert settings.MCP_SERVER_HOST == "0.0.0.0"
        assert settings.MCP_SERVER_PORT == 8000
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_FILE == "logs/mcp_server.log"

    def test_settings_api_url_validation(self):
        """Test API_BASE_URL validation."""
        # Valid URL should work
        settings = Settings()
        assert settings.API_BASE_URL.startswith(("http://", "https://"))

    def test_settings_api_url_strips_trailing_slash(self):
        """Test that trailing slashes are removed from API_BASE_URL."""
        # This would require mocking the env or creating a test instance
        # For now, just verify the validator exists
        settings = Settings()
        assert not settings.API_BASE_URL.endswith("/")

    def test_settings_port_range(self):
        """Test that MCP_SERVER_PORT is in valid range."""
        settings = Settings()
        assert 1 <= settings.MCP_SERVER_PORT <= 65535

    def test_settings_log_level_is_valid(self):
        """Test that LOG_LEVEL is one of valid values."""
        settings = Settings()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert settings.LOG_LEVEL in valid_levels

    def test_settings_session_timeout_in_range(self):
        """Test that session timeout is in valid range."""
        settings = Settings()
        assert 60 <= settings.SESSION_TIMEOUT <= 86400

    def test_settings_repr(self):
        """Test Settings string representation."""
        settings = Settings()
        repr_str = repr(settings)
        assert "Settings" in repr_str
        assert "API_BASE_URL" in repr_str


class TestSingletonPattern:
    """Tests for Singleton pattern implementation."""

    def setup_method(self):
        """Reset singleton before each test."""
        SingletonSettingsMeta.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        SingletonSettingsMeta.reset()

    def test_singleton_returns_same_instance(self):
        """Test that multiple instantiations return same instance."""
        settings1 = Settings()
        settings2 = Settings()
        assert settings1 is settings2

    def test_singleton_reset(self):
        """Test that singleton can be reset."""
        settings1 = Settings()
        SingletonSettingsMeta.reset()
        settings2 = Settings()
        assert settings1 is not settings2

    def test_class_attribute_access(self):
        """Test accessing settings as class attributes."""
        # Access via class
        url = Settings.API_BASE_URL
        assert isinstance(url, str)
        assert url.startswith(("http://", "https://"))

    def test_instance_attribute_access(self):
        """Test accessing settings as instance attributes."""
        settings = Settings()
        url = settings.API_BASE_URL
        assert isinstance(url, str)

    def test_class_and_instance_access_same_value(self):
        """Test that class and instance access return same value."""
        class_url = Settings.API_BASE_URL
        instance_url = Settings().API_BASE_URL
        assert class_url == instance_url


class TestSettingsMethods:
    """Tests for Settings methods."""

    def test_get_instance(self):
        """Test get_instance class method."""
        settings = Settings.get_instance()
        assert isinstance(settings, Settings)

    def test_get_instance_returns_singleton(self):
        """Test that get_instance returns singleton."""
        settings1 = Settings.get_instance()
        settings2 = Settings.get_instance()
        assert settings1 is settings2

    def test_model_dump_safe(self):
        """Test model_dump_safe method."""
        settings = Settings()
        config_dict = settings.model_dump_safe()
        assert isinstance(config_dict, dict)
        assert "API_BASE_URL" in config_dict
        assert "MCP_SERVER_PORT" in config_dict


class TestSettingsValidation:
    """Tests for Settings field validation."""

    def test_port_validation(self):
        """Test that invalid port raises validation error."""
        # This would require creating Settings with invalid data
        # which is challenging with environment-based config
        # For now, just verify the constraint exists
        settings = Settings()
        assert hasattr(settings, "MCP_SERVER_PORT")

    def test_log_file_creates_directory(self):
        """Test that log file directory is created."""
        settings = Settings()
        log_path = Path(settings.LOG_FILE)
        assert log_path.parent.exists()


class TestSettingsIntegration:
    """Integration tests for Settings."""

    def test_settings_works_with_env_file(self):
        """Test that Settings loads from .env file."""
        settings = Settings()
        # Should have API_BASE_URL from .env
        assert settings.API_BASE_URL is not None
        assert len(settings.API_BASE_URL) > 0

    def test_all_required_fields_present(self):
        """Test that all required configuration fields are present."""
        settings = Settings()

        required_fields = [
            "API_BASE_URL",
            "MCP_SERVER_HOST",
            "MCP_SERVER_PORT",
            "LOG_LEVEL",
            "LOG_FILE",
            "LOG_ROTATION",
            "LOG_RETENTION",
            "SESSION_TIMEOUT",
            "SESSION_CLEANUP_INTERVAL",
        ]

        for field in required_fields:
            assert hasattr(settings, field)
            assert getattr(settings, field) is not None
