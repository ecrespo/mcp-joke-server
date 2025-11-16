from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LoggerProtocol(Protocol):
    """
    Defines a protocol to standardize logging behavior across different logging implementations.

    The `LoggerProtocol` class is a runtime-checkable protocol that describes logging functions commonly
    utilized in applications. It serves as a base template for creating custom logger classes that comply
    with structured logging requirements. This protocol ensures that any implementing logger includes
    method signatures for logging messages at various levels, such as debug, info, warning, error,
    exception, and success.

    Implemented logging methods allow developers to log messages with optional arguments and keyword
    arguments, providing a consistent interface for all loggers across projects.
    """

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None: ...
    def success(self, msg: str, *args: Any, **kwargs: Any) -> None: ...


@runtime_checkable
class ConsoleRendererProtocol(Protocol):
    """
    Summary of what the class does.

    This protocol defines the interface for a console renderer, providing methods
    to render various types of components such as sections, tables, JSON data,
    panels, trees, and status messages. It specifies a set of methods that must
    be implemented by any class adhering to this protocol. This allows flexibility
    and consistency in rendering structured data or messages in console applications.

    """

    def section(self, title: str, style: str = "bold cyan") -> None: ...
    def table(self, title: str, data: Mapping[str, Any], style: str = "cyan") -> None: ...
    def json(self, data: Mapping[str, Any], title: str = "JSON Data") -> None: ...
    def panel(self, message: str, title: str | None = None, style: str = "cyan") -> None: ...
    def tree(self, data: Any, title: str = "Tree View") -> None: ...
    def status(self, message: str, spinner: str = "dots") -> Any: ...


__all__ = ["LoggerProtocol", "ConsoleRendererProtocol"]
