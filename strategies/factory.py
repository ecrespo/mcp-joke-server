"""
Transport Strategy Factory.

This module implements the Factory Pattern for creating transport strategies.
It provides a centralized way to instantiate the appropriate strategy based
on configuration, ensuring type safety and reducing coupling.
"""

from enum import Enum
from typing import Type, Dict
from strategies.base import TransportStrategy, TransportConfig
from strategies.stdio_strategy import StdioTransportStrategy
from strategies.http_strategy import HttpTransportStrategy
from strategies.sse_strategy import SseTransportStrategy
from utils.logger import log


class TransportType(str, Enum):
    """
    Enumeration of supported transport types.

    This enum provides type-safe transport type selection
    and prevents typos or invalid transport names.

    :cvar STDIO: Standard input/output transport
    :cvar HTTP: HTTP (streamable-http) transport
    :cvar SSE: Server-Sent Events transport
    """
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"

    @classmethod
    def from_string(cls, value: str) -> "TransportType":
        """
        Convert a string to TransportType enum.

        :param value: Transport type as string (case-insensitive)
        :type value: str
        :return: Corresponding TransportType enum value
        :rtype: TransportType
        :raises ValueError: If the value is not a valid transport type
        """
        value_lower = value.lower()
        try:
            return cls(value_lower)
        except ValueError:
            valid_types = ", ".join([t.value for t in cls])
            raise ValueError(
                f"Invalid transport type: {value!r}. "
                f"Must be one of: {valid_types}"
            )


class TransportStrategyFactory:
    """
    Factory for creating transport strategy instances.

    This class implements the Factory Pattern, providing a centralized
    way to create transport strategies. It maintains a registry of
    available strategies and handles instantiation with proper configuration.

    The factory ensures:
    - Type-safe strategy creation
    - Proper configuration injection
    - Consistent error handling
    - Easy extensibility for new transports

    Example usage:
        >>> config = TransportConfig(host="0.0.0.0", port=8000)
        >>> factory = TransportStrategyFactory()
        >>> strategy = factory.create(TransportType.HTTP, config)
        >>> strategy.validate()
        True

    :cvar _strategy_registry: Maps transport types to strategy classes
    :type _strategy_registry: Dict[TransportType, Type[TransportStrategy]]
    """

    # Registry mapping transport types to their strategy implementations
    _strategy_registry: Dict[TransportType, Type[TransportStrategy]] = {
        TransportType.STDIO: StdioTransportStrategy,
        TransportType.HTTP: HttpTransportStrategy,
        TransportType.SSE: SseTransportStrategy,
    }

    @classmethod
    def create(
        cls,
        transport_type: TransportType | str,
        config: TransportConfig
    ) -> TransportStrategy:
        """
        Create a transport strategy instance.

        This method instantiates the appropriate strategy class
        based on the transport type and injects the configuration.

        :param transport_type: Type of transport to create
        :type transport_type: TransportType | str
        :param config: Configuration for the transport
        :type config: TransportConfig
        :return: Instantiated transport strategy
        :rtype: TransportStrategy
        :raises ValueError: If transport_type is invalid
        """
        # Convert string to enum if necessary
        if isinstance(transport_type, str):
            transport_type = TransportType.from_string(transport_type)

        # Get the strategy class from registry
        strategy_class = cls._strategy_registry.get(transport_type)

        if strategy_class is None:
            valid_types = ", ".join([t.value for t in TransportType])
            raise ValueError(
                f"No strategy registered for transport type: {transport_type}. "
                f"Valid types: {valid_types}"
            )

        # Instantiate and return the strategy
        log.debug(f"Creating {strategy_class.__name__} with config: {config}")
        strategy = strategy_class(config)

        return strategy

    @classmethod
    def register_strategy(
        cls,
        transport_type: TransportType,
        strategy_class: Type[TransportStrategy]
    ) -> None:
        """
        Register a new transport strategy.

        This method allows extending the factory with custom
        transport strategies at runtime.

        :param transport_type: Transport type identifier
        :type transport_type: TransportType
        :param strategy_class: Strategy class to register
        :type strategy_class: Type[TransportStrategy]
        :raises TypeError: If strategy_class is not a TransportStrategy subclass
        """
        if not issubclass(strategy_class, TransportStrategy):
            raise TypeError(
                f"Strategy class must be a subclass of TransportStrategy, "
                f"got {strategy_class}"
            )

        log.info(
            f"Registering custom strategy: {strategy_class.__name__} "
            f"for transport type {transport_type.value}"
        )
        cls._strategy_registry[transport_type] = strategy_class

    @classmethod
    def get_available_transports(cls) -> list[str]:
        """
        Get a list of available transport types.

        :return: List of transport type names
        :rtype: list[str]
        """
        return [transport.value for transport in cls._strategy_registry.keys()]


def create_transport_strategy(
    transport_type: TransportType | str,
    config: TransportConfig | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    show_banner: bool = True,
) -> TransportStrategy:
    """
    Create a transport strategy with explicit dependency injection.

    This helper avoids reading global Settings and instead accepts the
    transport type and configuration explicitly. Prefer this in
    application code to reduce coupling to environment/config singletons.

    :param transport_type: Transport type (enum or string: "stdio"|"http"|"sse")
    :param config: Optional TransportConfig. If not provided, one is
                   constructed from host/port/show_banner.
    :param host: Host for HTTP/SSE transports (ignored by stdio)
    :param port: Port for HTTP/SSE transports (ignored by stdio)
    :param show_banner: Whether to show FastMCP banner on start
    :return: Configured transport strategy instance
    :raises ValueError: If arguments are invalid
    """
    # Prepare configuration
    if config is None:
        # Fallback sane defaults if host/port are not given
        config = TransportConfig(
            host=host or "0.0.0.0",
            port=port or 8000,
            show_banner=show_banner,
        )

    # Delegate to factory
    return TransportStrategyFactory.create(transport_type, config)


def create_transport_strategy_from_settings() -> TransportStrategy:
    """
    Create a transport strategy from application settings.

    This convenience function reads the transport configuration
    from the Settings singleton and creates the appropriate strategy.

    :return: Configured transport strategy
    :rtype: TransportStrategy
    :raises ValueError: If settings contain invalid configuration
    """
    from utils.config import Settings

    # Get transport type from settings
    transport_type = TransportType.from_string(Settings.MCP_PROTOCOL)

    # Create configuration
    config = TransportConfig(
        host=Settings.MCP_SERVER_HOST,
        port=Settings.MCP_SERVER_PORT,
        show_banner=True,
    )

    # Create and return strategy (delegates to DI-friendly helper)
    log.info(f"Creating transport strategy: {transport_type.value}")
    strategy = create_transport_strategy(transport_type, config)

    # Validate before returning
    strategy.validate()

    return strategy
