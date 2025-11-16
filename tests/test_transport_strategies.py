"""
Tests for Transport Strategy Pattern implementation.

This module tests the Strategy Pattern implementation for MCP transport protocols,
ensuring that all strategies work correctly and the factory creates appropriate instances.
"""

import pytest
from unittest.mock import patch, MagicMock
import socket

from strategies import (
    TransportConfig,
    TransportStrategy,
    StdioTransportStrategy,
    HttpTransportStrategy,
    SseTransportStrategy,
    TransportStrategyFactory,
    TransportType,
    create_transport_strategy_from_settings,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def basic_config():
    """Basic transport configuration."""
    return TransportConfig(
        host="localhost",
        port=8000,
        show_banner=False
    )


@pytest.fixture
def http_config():
    """Configuration for HTTP transport."""
    return TransportConfig(
        host="0.0.0.0",
        port=8080,
        show_banner=True
    )


@pytest.fixture
def stdio_strategy(basic_config):
    """Stdio transport strategy instance."""
    return StdioTransportStrategy(basic_config)


@pytest.fixture
def http_strategy(http_config):
    """HTTP transport strategy instance."""
    return HttpTransportStrategy(http_config)


@pytest.fixture
def sse_strategy(basic_config):
    """SSE transport strategy instance."""
    return SseTransportStrategy(basic_config)


# ============================================================================
# TransportConfig Tests
# ============================================================================

class TestTransportConfig:
    """Tests for TransportConfig data class."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TransportConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.show_banner is True
        assert config.additional_options == {}

    def test_custom_values(self):
        """Test custom configuration values."""
        config = TransportConfig(
            host="localhost",
            port=9000,
            show_banner=False,
            additional_options={"timeout": 30}
        )
        assert config.host == "localhost"
        assert config.port == 9000
        assert config.show_banner is False
        assert config.additional_options == {"timeout": 30}

    def test_immutability(self):
        """Test that config is immutable (frozen dataclass)."""
        config = TransportConfig()
        with pytest.raises(AttributeError):
            config.port = 9000

    def test_invalid_port_range(self):
        """Test validation of port range."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            TransportConfig(port=0)

        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            TransportConfig(port=70000)

    def test_none_additional_options(self):
        """Test that None additional_options is converted to empty dict."""
        config = TransportConfig(additional_options=None)
        assert config.additional_options == {}


# ============================================================================
# StdioTransportStrategy Tests
# ============================================================================

class TestStdioTransportStrategy:
    """Tests for STDIO transport strategy."""

    def test_transport_name(self, stdio_strategy):
        """Test that transport name is correct."""
        assert stdio_strategy.get_transport_name() == "stdio"

    def test_transport_kwargs(self, stdio_strategy):
        """Test that transport kwargs are correct."""
        kwargs = stdio_strategy.get_transport_kwargs()
        assert kwargs["transport"] == "stdio"
        assert kwargs["show_banner"] is False
        assert "host" not in kwargs  # STDIO doesn't need host
        assert "port" not in kwargs  # STDIO doesn't need port

    def test_transport_kwargs_with_additional_options(self):
        """Test kwargs with additional options."""
        config = TransportConfig(
            additional_options={"custom_option": "value"}
        )
        strategy = StdioTransportStrategy(config)
        kwargs = strategy.get_transport_kwargs()
        assert kwargs["custom_option"] == "value"

    def test_validate(self, stdio_strategy):
        """Test validation always passes for STDIO."""
        assert stdio_strategy.validate() is True

    def test_prepare(self, stdio_strategy):
        """Test prepare method executes without errors."""
        # Should not raise any exceptions
        stdio_strategy.prepare()

    def test_repr(self, stdio_strategy):
        """Test string representation."""
        repr_str = repr(stdio_strategy)
        assert "StdioTransportStrategy" in repr_str
        assert "stdio" in repr_str


# ============================================================================
# HttpTransportStrategy Tests
# ============================================================================

class TestHttpTransportStrategy:
    """Tests for HTTP transport strategy."""

    def test_transport_name(self, http_strategy):
        """Test that transport name is correct."""
        assert http_strategy.get_transport_name() == "streamable-http"

    def test_transport_kwargs(self, http_strategy):
        """Test that transport kwargs are correct."""
        kwargs = http_strategy.get_transport_kwargs()
        assert kwargs["transport"] == "streamable-http"
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8080
        assert kwargs["show_banner"] is True

    def test_transport_kwargs_with_additional_options(self):
        """Test kwargs with additional options."""
        config = TransportConfig(
            host="localhost",
            port=8000,
            additional_options={"ssl": True}
        )
        strategy = HttpTransportStrategy(config)
        kwargs = strategy.get_transport_kwargs()
        assert kwargs["ssl"] is True

    @patch.object(HttpTransportStrategy, '_is_port_available', return_value=True)
    @patch.object(HttpTransportStrategy, '_is_valid_host', return_value=True)
    def test_validate_success(self, mock_host, mock_port, http_strategy):
        """Test successful validation."""
        assert http_strategy.validate() is True
        mock_port.assert_called_once()
        mock_host.assert_called_once()

    @patch.object(HttpTransportStrategy, '_is_port_available', return_value=False)
    def test_validate_port_unavailable(self, mock_port, http_strategy):
        """Test validation fails when port is unavailable."""
        with pytest.raises(ValueError, match="Port .* is already in use"):
            http_strategy.validate()

    @patch.object(HttpTransportStrategy, '_is_port_available', return_value=True)
    @patch.object(HttpTransportStrategy, '_is_valid_host', return_value=False)
    def test_validate_invalid_host(self, mock_host, mock_port, http_strategy):
        """Test validation fails for invalid host."""
        with pytest.raises(ValueError, match="Invalid host address"):
            http_strategy.validate()

    def test_is_valid_host_special_values(self):
        """Test host validation for special host values."""
        config = TransportConfig(host="0.0.0.0", port=8000)
        strategy = HttpTransportStrategy(config)
        assert strategy._is_valid_host() is True

        config = TransportConfig(host="localhost", port=8000)
        strategy = HttpTransportStrategy(config)
        assert strategy._is_valid_host() is True

    def test_prepare(self, http_strategy):
        """Test prepare method executes without errors."""
        # Should not raise any exceptions
        http_strategy.prepare()

    def test_repr(self, http_strategy):
        """Test string representation."""
        repr_str = repr(http_strategy)
        assert "HttpTransportStrategy" in repr_str
        assert "streamable-http" in repr_str


# ============================================================================
# SseTransportStrategy Tests
# ============================================================================

class TestSseTransportStrategy:
    """Tests for SSE transport strategy."""

    def test_transport_name(self, sse_strategy):
        """Test that transport name is correct."""
        assert sse_strategy.get_transport_name() == "sse"

    def test_transport_kwargs(self, sse_strategy):
        """Test that transport kwargs are correct."""
        kwargs = sse_strategy.get_transport_kwargs()
        assert kwargs["transport"] == "sse"
        assert kwargs["host"] == "localhost"
        assert kwargs["port"] == 8000
        assert kwargs["show_banner"] is False

    @patch.object(SseTransportStrategy, '_is_port_available', return_value=True)
    @patch.object(SseTransportStrategy, '_is_valid_host', return_value=True)
    def test_validate_success(self, mock_host, mock_port, sse_strategy):
        """Test successful validation."""
        assert sse_strategy.validate() is True

    def test_prepare(self, sse_strategy):
        """Test prepare method executes without errors."""
        # Should not raise any exceptions
        sse_strategy.prepare()


# ============================================================================
# TransportType Enum Tests
# ============================================================================

class TestTransportType:
    """Tests for TransportType enum."""

    def test_enum_values(self):
        """Test enum has correct values."""
        assert TransportType.STDIO.value == "stdio"
        assert TransportType.HTTP.value == "http"
        assert TransportType.SSE.value == "sse"

    def test_from_string_valid(self):
        """Test creating enum from valid strings."""
        assert TransportType.from_string("stdio") == TransportType.STDIO
        assert TransportType.from_string("http") == TransportType.HTTP
        assert TransportType.from_string("sse") == TransportType.SSE

    def test_from_string_case_insensitive(self):
        """Test from_string is case-insensitive."""
        assert TransportType.from_string("STDIO") == TransportType.STDIO
        assert TransportType.from_string("Http") == TransportType.HTTP
        assert TransportType.from_string("SSE") == TransportType.SSE

    def test_from_string_invalid(self):
        """Test from_string raises error for invalid value."""
        with pytest.raises(ValueError, match="Invalid transport type"):
            TransportType.from_string("invalid")


# ============================================================================
# TransportStrategyFactory Tests
# ============================================================================

class TestTransportStrategyFactory:
    """Tests for TransportStrategyFactory."""

    def test_create_stdio_strategy(self, basic_config):
        """Test creating STDIO strategy."""
        strategy = TransportStrategyFactory.create(TransportType.STDIO, basic_config)
        assert isinstance(strategy, StdioTransportStrategy)
        assert strategy.config == basic_config

    def test_create_http_strategy(self, http_config):
        """Test creating HTTP strategy."""
        strategy = TransportStrategyFactory.create(TransportType.HTTP, http_config)
        assert isinstance(strategy, HttpTransportStrategy)
        assert strategy.config == http_config

    def test_create_sse_strategy(self, basic_config):
        """Test creating SSE strategy."""
        strategy = TransportStrategyFactory.create(TransportType.SSE, basic_config)
        assert isinstance(strategy, SseTransportStrategy)

    def test_create_from_string(self, basic_config):
        """Test creating strategy from string."""
        strategy = TransportStrategyFactory.create("stdio", basic_config)
        assert isinstance(strategy, StdioTransportStrategy)

        strategy = TransportStrategyFactory.create("http", basic_config)
        assert isinstance(strategy, HttpTransportStrategy)

    def test_create_invalid_type(self, basic_config):
        """Test creating strategy with invalid type."""
        with pytest.raises(ValueError, match="Invalid transport type"):
            TransportStrategyFactory.create("invalid", basic_config)

    def test_get_available_transports(self):
        """Test getting available transport types."""
        transports = TransportStrategyFactory.get_available_transports()
        assert "stdio" in transports
        assert "http" in transports
        assert "sse" in transports
        assert len(transports) == 3

    def test_register_custom_strategy(self, basic_config):
        """Test registering a custom strategy."""
        class CustomStrategy(TransportStrategy):
            def get_transport_name(self):
                return "custom"

            def get_transport_kwargs(self):
                return {"transport": "custom"}

        # Create a new transport type (in real scenario you'd extend the enum)
        # For testing, we'll use one of existing types
        TransportStrategyFactory.register_strategy(
            TransportType.STDIO,  # Temporarily override
            CustomStrategy
        )

        strategy = TransportStrategyFactory.create(TransportType.STDIO, basic_config)
        assert isinstance(strategy, CustomStrategy)

        # Restore original (important for other tests)
        TransportStrategyFactory._strategy_registry[TransportType.STDIO] = StdioTransportStrategy

    def test_register_invalid_strategy_class(self):
        """Test registering non-TransportStrategy class fails."""
        class NotAStrategy:
            pass

        with pytest.raises(TypeError, match="must be a subclass of TransportStrategy"):
            TransportStrategyFactory.register_strategy(
                TransportType.STDIO,
                NotAStrategy
            )


# ============================================================================
# Integration Tests
# ============================================================================

class TestTransportStrategyIntegration:
    """Integration tests for transport strategies."""

    def test_create_from_settings_stdio(self, monkeypatch):
        """Test creating strategy from settings (stdio)."""
        # Use monkeypatch to override Settings attributes
        from utils.config import Settings
        monkeypatch.setattr(Settings, 'MCP_PROTOCOL', 'stdio', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_HOST', 'localhost', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_PORT', 8000, raising=False)

        strategy = create_transport_strategy_from_settings()
        assert isinstance(strategy, StdioTransportStrategy)
        assert strategy.config.host == "localhost"
        assert strategy.config.port == 8000

    @patch.object(HttpTransportStrategy, 'validate', return_value=True)
    def test_create_from_settings_http(self, mock_validate, monkeypatch):
        """Test creating strategy from settings (http)."""
        from utils.config import Settings
        monkeypatch.setattr(Settings, 'MCP_PROTOCOL', 'http', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_HOST', '0.0.0.0', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_PORT', 9000, raising=False)

        strategy = create_transport_strategy_from_settings()
        assert isinstance(strategy, HttpTransportStrategy)
        assert strategy.config.host == "0.0.0.0"
        assert strategy.config.port == 9000
        mock_validate.assert_called_once()

    @patch.object(SseTransportStrategy, 'validate', return_value=True)
    def test_create_from_settings_sse(self, mock_validate, monkeypatch):
        """Test creating strategy from settings (sse)."""
        from utils.config import Settings
        monkeypatch.setattr(Settings, 'MCP_PROTOCOL', 'sse', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_HOST', '127.0.0.1', raising=False)
        monkeypatch.setattr(Settings, 'MCP_SERVER_PORT', 8080, raising=False)

        strategy = create_transport_strategy_from_settings()
        assert isinstance(strategy, SseTransportStrategy)
        assert strategy.config.host == "127.0.0.1"
        assert strategy.config.port == 8080
        mock_validate.assert_called_once()

    def test_end_to_end_stdio(self):
        """Test end-to-end flow for stdio transport."""
        config = TransportConfig(show_banner=False)
        strategy = TransportStrategyFactory.create(TransportType.STDIO, config)

        # Prepare and validate
        strategy.prepare()
        assert strategy.validate() is True

        # Get kwargs for mcp.run()
        kwargs = strategy.get_transport_kwargs()
        assert kwargs["transport"] == "stdio"
        assert kwargs["show_banner"] is False

    @patch.object(HttpTransportStrategy, '_is_port_available', return_value=True)
    @patch.object(HttpTransportStrategy, '_is_valid_host', return_value=True)
    def test_end_to_end_http(self, mock_host, mock_port):
        """Test end-to-end flow for HTTP transport."""
        config = TransportConfig(host="localhost", port=8888, show_banner=True)
        strategy = TransportStrategyFactory.create(TransportType.HTTP, config)

        # Prepare and validate
        strategy.prepare()
        assert strategy.validate() is True

        # Get kwargs for mcp.run()
        kwargs = strategy.get_transport_kwargs()
        assert kwargs["transport"] == "streamable-http"
        assert kwargs["host"] == "localhost"
        assert kwargs["port"] == 8888
        assert kwargs["show_banner"] is True
