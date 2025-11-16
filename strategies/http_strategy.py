"""
HTTP Transport Strategy Implementation.

This module implements the HTTP (streamable-http) transport strategy
for MCP servers. This transport allows the server to be accessed over HTTP,
enabling remote clients to connect to the MCP server.
"""

from typing import Dict, Any
import socket
from strategies.base import TransportStrategy, TransportConfig
from utils.logger import log


class HttpTransportStrategy(TransportStrategy):
    """
    HTTP transport strategy for MCP servers.

    This strategy uses HTTP (specifically "streamable-http") for communication,
    allowing the MCP server to accept remote connections over a network.
    It's suitable for multi-client scenarios and remote access.

    Features:
    - Network-accessible server
    - Supports multiple concurrent clients
    - Configurable host and port
    - Suitable for distributed systems and remote access

    Example usage:
        >>> config = TransportConfig(host="0.0.0.0", port=8000)
        >>> strategy = HttpTransportStrategy(config)
        >>> strategy.validate()  # Checks if port is available
        True
        >>> kwargs = strategy.get_transport_kwargs()
        >>> # Pass kwargs to mcp.run(**kwargs)

    :ivar config: Transport configuration with host and port
    :type config: TransportConfig
    """

    def get_transport_name(self) -> str:
        """
        Get the transport name for HTTP.

        :return: "streamable-http"
        :rtype: str
        """
        return "streamable-http"

    def get_transport_kwargs(self) -> Dict[str, Any]:
        """
        Get keyword arguments for HTTP transport.

        HTTP transport requires host and port configuration
        in addition to the transport type.

        :return: Dictionary with transport, host, port, and show_banner
        :rtype: Dict[str, Any]
        """
        kwargs = {
            "transport": self.get_transport_name(),
            "host": self.config.host,
            "port": self.config.port,
            "show_banner": self.config.show_banner,
        }

        # Add any additional options
        if self.config.additional_options:
            kwargs.update(self.config.additional_options)

        return kwargs

    def prepare(self) -> None:
        """
        Prepare HTTP transport.

        Logs the server configuration and validates that the
        port is available before starting.
        """
        log.debug(f"Preparing {self.get_transport_name()} transport")
        log.info(f"Server will listen on {self.config.host}:{self.config.port}")
        log.debug(f"Show banner: {self.config.show_banner}")

    def validate(self) -> bool:
        """
        Validate HTTP transport configuration.

        Checks that:
        1. Port is in valid range (1-65535)
        2. Port is available (not already in use)
        3. Host address is valid

        :return: True if configuration is valid
        :rtype: bool
        :raises ValueError: If configuration is invalid
        """
        log.info(f"Validating {self.get_transport_name()} transport configuration")

        # Port validation (already done in TransportConfig, but double-check)
        if not (1 <= self.config.port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {self.config.port}")

        # Check if port is available
        if not self._is_port_available():
            raise ValueError(
                f"Port {self.config.port} is already in use on {self.config.host}. "
                "Please choose a different port or stop the service using this port."
            )

        # Validate host address
        if not self._is_valid_host():
            raise ValueError(
                f"Invalid host address: {self.config.host}. "
                "Use a valid IP address or '0.0.0.0' for all interfaces."
            )

        log.info(f"HTTP transport configuration is valid")
        return True

    def _is_port_available(self) -> bool:
        """
        Check if the configured port is available.

        Attempts to bind to the port to verify it's not in use.

        :return: True if port is available, False otherwise
        :rtype: bool
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((self.config.host, self.config.port))
                return True
        except OSError as e:
            log.warning(
                f"Port {self.config.port} on {self.config.host} is not available: {e}"
            )
            return False

    def _is_valid_host(self) -> bool:
        """
        Validate the host address.

        Checks if the host is a valid IP address or special value
        like "0.0.0.0" (all interfaces) or "localhost".

        :return: True if host is valid
        :rtype: bool
        """
        # Special cases
        valid_special_hosts = {"0.0.0.0", "localhost", "127.0.0.1", "::"}

        if self.config.host in valid_special_hosts:
            return True

        # Try to validate as IPv4 or IPv6 address
        try:
            socket.inet_aton(self.config.host)  # IPv4
            return True
        except OSError:
            pass

        try:
            socket.inet_pton(socket.AF_INET6, self.config.host)  # IPv6
            return True
        except OSError:
            pass

        # Could also be a hostname - try to resolve it
        try:
            socket.gethostbyname(self.config.host)
            return True
        except OSError:
            log.error(f"Cannot resolve host: {self.config.host}")
            return False
