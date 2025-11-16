"""
Transport Strategy Pattern - Base Classes.

This module defines the abstract base class for MCP transport strategies,
implementing the Strategy Pattern to allow flexible switching between
different transport protocols (stdio, HTTP, SSE) without changing the
core application logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


@dataclass(frozen=True)
class TransportConfig:
    """
    Configuration data for transport strategies.

    This immutable data class holds the configuration parameters
    needed by different transport strategies.

    :ivar host: Server host address (used by HTTP/SSE transports)
    :type host: str
    :ivar port: Server port number (used by HTTP/SSE transports)
    :type port: int
    :ivar show_banner: Whether to show the FastMCP startup banner
    :type show_banner: bool
    :ivar additional_options: Additional transport-specific options
    :type additional_options: Dict[str, Any]
    """
    host: str = "0.0.0.0"
    port: int = 8000
    show_banner: bool = True
    additional_options: Dict[str, Any] | None = None

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {self.port}")

        # Convert None to empty dict for additional_options
        if self.additional_options is None:
            object.__setattr__(self, 'additional_options', {})


class TransportStrategy(ABC):
    """
    Abstract base class for MCP transport strategies.

    This class defines the interface that all concrete transport strategies
    must implement. It follows the Strategy Pattern, allowing the transport
    mechanism to be selected and changed at runtime.

    Concrete implementations should handle:
    - stdio transport (standard input/output)
    - HTTP transport (streamable-http)
    - SSE transport (server-sent events)

    :ivar config: Transport configuration
    :type config: TransportConfig
    """

    def __init__(self, config: TransportConfig):
        """
        Initialize the transport strategy.

        :param config: Transport configuration parameters
        :type config: TransportConfig
        """
        self._config = config

    @property
    def config(self) -> TransportConfig:
        """Get the transport configuration."""
        return self._config

    @abstractmethod
    def get_transport_name(self) -> str:
        """
        Get the name of the transport protocol.

        This should return the transport name expected by FastMCP
        (e.g., "stdio", "streamable-http", "sse").

        :return: Transport protocol name
        :rtype: str
        """
        pass

    @abstractmethod
    def get_transport_kwargs(self) -> Dict[str, Any]:
        """
        Get the keyword arguments to pass to mcp.run().

        This method should return a dictionary of parameters specific
        to this transport strategy that will be passed to FastMCP's run() method.

        :return: Dictionary of transport-specific parameters
        :rtype: Dict[str, Any]
        """
        pass

    def prepare(self) -> None:
        """
        Prepare the transport before running.

        This method is called before starting the server and can be
        used for any setup tasks (e.g., creating directories, validating
        configuration, opening connections).

        Override this method in subclasses if preparation is needed.
        """
        pass

    def validate(self) -> bool:
        """
        Validate the transport configuration.

        This method checks if the transport is properly configured
        and can be used. Override in subclasses for specific validation.

        :return: True if configuration is valid
        :rtype: bool
        :raises ValueError: If configuration is invalid
        """
        return True

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return f"{self.__class__.__name__}(transport={self.get_transport_name()!r})"
