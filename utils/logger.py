from __future__ import annotations

# Fachada mínima: delega en piezas especializadas
from rich.traceback import install as install_rich_traceback

from utils.logging_config import configure_logger
from utils.logging_interfaces import ConsoleRendererProtocol, LoggerProtocol
from utils.rich_renderers import RichConsoleRenderer


def setup_logger() -> LoggerProtocol:
    """Configura y devuelve la instancia de logger.

    Patrón aplicado: Fachada + Inversión de Dependencias.
    - La configuración real vive en `utils.logging_config`.
    - La "vista" (salida rica) vive en `utils.rich_renderers` y es inyectada
      únicamente como función `write`, evitando dependencias circulares.
    """
    _renderer = RichConsoleRenderer()
    return configure_logger(_renderer.write)


def get_view() -> ConsoleRendererProtocol:
    """Devuelve la vista/renderer de consola (protocolo ConsoleRendererProtocol).

    Esto permite usar helpers Rich sin acoplar el resto del código a funciones
    globales. Preferir `from utils.logger import view` o `get_view()` y luego
    `view.section(...)`, `view.table(...)`, etc.
    """
    return renderer


class LogContext:
    """
    Provides a context manager for logging sections with a specified title and style.

    This class simplifies logging by marking the beginning and the end of a
    specific code section. It supports customizable styles for text formatting
    and ensures that any exceptions raised within the context are also logged
    appropriately.

    :ivar title: The title of the log section.
    :type title: str
    :ivar style: The style of the log section's title. Defaults to "cyan".
    :type style: str
    """

    def __init__(self, title: str, style: str = "cyan"):
        self.title = title
        self.style = style

    def __enter__(self):
        renderer.section(f"BEGIN: {self.title}", self.style)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            renderer.section(f"END: {self.title} ✓", "green")
        else:
            renderer.section(f"END: {self.title} ✗", "red")
        return False


# Instalamos rich traceback y exponemos una instancia global por compatibilidad
install_rich_traceback(show_locals=True)

# Renderer y logger globales (fachada mínima)
renderer: ConsoleRendererProtocol = RichConsoleRenderer()
log: LoggerProtocol = configure_logger(renderer.write)
console = renderer.console  # reexportamos la consola rica para compatibilidad

__all__ = ["log", "console", "get_view", "renderer", "LogContext"]
