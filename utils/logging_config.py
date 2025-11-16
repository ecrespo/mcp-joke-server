from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger as _loguru_logger

from utils.config import Settings


def format_record(record: dict) -> str:
    """
    Formats a log record into a colored string using the `rich` library.

    This function processes the given log record dictionary to generate a
    human-readable, timestamped, and formatted string using specified level
    colors and escapes special characters for proper display.

    :param record: The log record dictionary containing details such as
        level, name, function, line, message, and timestamp.
    :type record: dict
    :return: A formatted string representing the log record with color-coded
        level indicators and escaped message content for display.
    :rtype: str
    """
    from rich.markup import escape

    level_colors = {
        "TRACE": "dim blue",
        "DEBUG": "cyan",
        "INFO": "green",
        "SUCCESS": "bold green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold white on red",
    }

    level = record["level"].name
    level_color = level_colors.get(level, "white")
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    file_info = f"{record['name']}:{record['function']}:{record['line']}"
    message = escape(str(record["message"])).replace("{", "{{").replace("}", "}}")

    return (
        f"[dim cyan]{timestamp}[/dim cyan] | "
        f"[{level_color}]{level: <8}[/{level_color}] | "
        f"[dim blue]{file_info}[/dim blue] - "
        f"[white]{message}[/white]"
    )


class _RichSink:
    """
    Handles message output using a callable write function.

    Provides a mechanism to send formatted string messages to a provided
    write function. The primary purpose of this class is to process
    and forward messages with formatting and stripping as necessary.

    """

    def __init__(self, write_func: Callable[[str], Any]):
        self._write = write_func

    def __call__(self, message: str) -> None:
        # Loguru puede enviar un objeto con .strip(), aseguramos str
        msg = str(message).rstrip()
        if msg:
            self._write(msg)


def configure_logger(console_write: Callable[[str], Any]) -> _loguru_logger.__class__:
    """
    Configures the logger with both console and file sinks, using the settings from
    the `Settings` class. This function sets up a single instance of a logger
    with specific configurations for formatting, log levels, console writing,
    log rotation, and retention policies.

    :param console_write: Function to handle console output for the logger.
    :type console_write: Callable[[str], Any]

    :return: The configured logger instance.
    :rtype: loguru.Logger
    """

    settings = Settings()

    _loguru_logger.remove()

    # Consola (via sink inyectable)
    _loguru_logger.add(
        _RichSink(console_write),
        format=format_record,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Archivo principal
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    _loguru_logger.add(
        settings.LOG_FILE,
        format=file_format,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    # Archivo de errores
    error_log_file = log_path.parent / "errors.log"
    _loguru_logger.add(
        str(error_log_file),
        format=file_format,
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    _loguru_logger.info("✨ Logger configurado")
    _loguru_logger.debug(f"📁 Logs: {settings.LOG_FILE}")
    _loguru_logger.debug(f"📊 Nivel: {settings.LOG_LEVEL}")

    return _loguru_logger


__all__ = ["configure_logger", "format_record"]
