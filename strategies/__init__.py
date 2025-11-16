"""
Transport Strategy Pattern Module.

This module implements the Strategy Pattern for MCP transport protocols,
allowing flexible switching between different transport mechanisms
(stdio, HTTP, SSE) without changing the core application logic.

Main components:
- TransportStrategy: Abstract base class defining the strategy interface
- TransportConfig: Configuration data class for transport strategies
- StdioTransportStrategy: STDIO transport implementation
- HttpTransportStrategy: HTTP (streamable-http) transport implementation
- SseTransportStrategy: SSE transport implementation
- TransportStrategyFactory: Factory for creating transport strategies
- TransportType: Enum of supported transport types

Quick start:
    >>> from strategies import create_transport_strategy_from_settings
    >>> strategy = create_transport_strategy_from_settings()
    >>> strategy.prepare()
    >>> kwargs = strategy.get_transport_kwargs()
    >>> # Pass kwargs to mcp.run(**kwargs)

Custom configuration:
    >>> from strategies import TransportConfig, TransportStrategyFactory, TransportType
    >>> config = TransportConfig(host="localhost", port=8080)
    >>> strategy = TransportStrategyFactory.create(TransportType.HTTP, config)
    >>> strategy.validate()
    True
"""

from strategies.base import TransportConfig, TransportStrategy
from strategies.factory import (
    TransportStrategyFactory,
    TransportType,
    create_transport_strategy_from_settings,
)
from strategies.http_strategy import HttpTransportStrategy
from strategies.sse_strategy import SseTransportStrategy
from strategies.stdio_strategy import StdioTransportStrategy

__all__ = [
    # Base classes
    "TransportStrategy",
    "TransportConfig",
    # Concrete strategies
    "StdioTransportStrategy",
    "HttpTransportStrategy",
    "SseTransportStrategy",
    # Factory
    "TransportStrategyFactory",
    "TransportType",
    "create_transport_strategy_from_settings",
]
