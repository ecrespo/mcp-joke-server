"""
STDIO Transport Strategy Implementation.

This module implements the STDIO (Standard Input/Output) transport strategy
for MCP servers. This is the default transport for MCP and communicates
via standard input and output streams.
"""

from typing import Dict, Any
from strategies.base import TransportStrategy, TransportConfig
from utils.logger import log


class StdioTransportStrategy(TransportStrategy):
    """
    STDIO transport strategy for MCP servers.

    This strategy uses standard input/output for communication,
    which is the default and most common transport for MCP.
    It's typically used when the MCP server is spawned as a subprocess
    by a client application.

    Features:
    - No network configuration required
    - Works with pipes and subprocess communication
    - Minimal overhead
    - Suitable for local, single-client scenarios

    Example usage:
        >>> config = TransportConfig(show_banner=False)
        >>> strategy = StdioTransportStrategy(config)
        >>> kwargs = strategy.get_transport_kwargs()
        >>> # Pass kwargs to mcp.run(**kwargs)
    """

    def get_transport_name(self) -> str:
        """
        Get the transport name for STDIO.

        :return: "stdio"
        :rtype: str
        """
        return "stdio"

    def get_transport_kwargs(self) -> Dict[str, Any]:
        """
        Get keyword arguments for STDIO transport.

        STDIO transport doesn't require host/port configuration,
        only the transport type and optional banner setting.

        :return: Dictionary with transport="stdio" and show_banner
        :rtype: Dict[str, Any]
        """
        kwargs = {
            "transport": self.get_transport_name(),
            "show_banner": self.config.show_banner,
        }

        # Add any additional options
        if self.config.additional_options:
            kwargs.update(self.config.additional_options)

        return kwargs

    def prepare(self) -> None:
        """
        Prepare STDIO transport.

        STDIO doesn't require special preparation, but we log
        the configuration for debugging purposes.
        """
        log.debug(f"Preparing {self.get_transport_name()} transport")
        log.debug(f"Show banner: {self.config.show_banner}")

    def validate(self) -> bool:
        """
        Validate STDIO transport configuration.

        STDIO has minimal configuration requirements,
        so validation always passes unless there are
        additional custom options that need validation.

        :return: True (STDIO is always valid)
        :rtype: bool
        """
        log.info(f"Validating {self.get_transport_name()} transport configuration")
        return True
