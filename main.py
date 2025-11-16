"""
MCP Joke Server - Main application module.

This module implements the FastMCP server with tools for fetching jokes
using the Repository Pattern for data access abstraction.
Authentication is enforced for HTTP/SSE transports via Bearer token.
"""

from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext
from pydantic import Field

from repositories import get_joke_repository
from utils.auth import LocalTokenValidator
from utils.constants import CONSISTENT_JOKE, JOKE_TYPES
from utils.formatters import extract_joke
from utils.logger import log
from utils.RequestAPIJokes import (
    aget_joke as api_aget_joke,
)
from utils.RequestAPIJokes import (
    aget_joke_by_id as api_aget_joke_by_id,
)
from utils.RequestAPIJokes import (
    aget_jokes_by_type as api_aget_jokes_by_type,
)


class LocalTokenAuthMiddleware(Middleware):
    """
    Middleware for authenticating requests using local bearer tokens.

    This middleware validates tokens from the Authorization header
    for HTTP and SSE transports. STDIO transport is not authenticated
    as it runs in a trusted local environment.
    """

    def __init__(self):
        super().__init__()
        self.validator = LocalTokenValidator()
        log.info("LocalTokenAuthMiddleware initialized")

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """
        Intercept tool calls to validate authentication token.

        Args:
            context: Middleware context with request information
            call_next: Function to call next middleware or tool

        Returns:
            Result from the tool if authenticated

        Raises:
            ToolError: If authentication fails
        """
        try:
            # Get HTTP request (will be None for stdio transport)
            request = get_http_request()

            if request is None:
                # STDIO transport - no authentication required
                log.debug("STDIO transport detected, skipping authentication")
                return await call_next(context)

            # Extract token from Authorization header
            auth_header = request.headers.get("authorization", "")

            if not auth_header:
                log.warning("Missing Authorization header")
                raise ToolError(
                    "Authentication required. Please provide a Bearer token in the Authorization header."
                )

            # Remove "Bearer " prefix
            if not auth_header.lower().startswith("bearer "):
                log.warning("Invalid Authorization header format")
                raise ToolError(
                    "Invalid Authorization header format. Expected: 'Bearer <token>'"
                )

            token = auth_header[7:].strip()  # Remove "Bearer " prefix

            # Validate token
            token_info = self.validator.validate_token(token)

            if not token_info:
                log.warning("Token validation failed")
                raise ToolError("Authentication failed. Invalid or expired token.")

            # Store token info in context for potential use in tools
            context.fastmcp_context.set_state("authenticated", True)
            context.fastmcp_context.set_state("auth_type", token_info.get("type"))

            log.info("Request authenticated successfully")

            # Proceed to the tool
            return await call_next(context)

        except ToolError:
            # Re-raise ToolError as-is
            raise
        except Exception as e:
            log.error(f"Unexpected error in authentication middleware: {e}")
            log.exception("Authentication middleware error details:")
            raise ToolError(f"Authentication error: {str(e)}")


# Initialize MCP server with authentication middleware
mcp = FastMCP("jokes (python)")
mcp.add_middleware(LocalTokenAuthMiddleware())

# Initialize joke repository (singleton pattern)
# Uses cached repository by default for better performance
joke_repo = get_joke_repository()


### Tools!


@mcp.tool
def tool_get_consistent_joke() -> str:
    """
    Fetches a consistent joke as a string, typically predefined or hardcoded.
    This function is designed to return the same joke every time it is called,
    ensuring consistency in its output.

    :return: A consistent joke in string format.
    :rtype: str
    """
    return CONSISTENT_JOKE


@mcp.tool
def tool_get_joke() -> str:
    """
    Fetches a random joke from the joke repository.

    This function uses the Repository Pattern to abstract data access,
    allowing for flexible data sources (HTTP API, cache, database, etc.)
    without changing the tool implementation.

    :return: A string containing the extracted joke.
    :rtype: str
    """
    joke = joke_repo.get_random_joke()
    # Evitar uso directo de __dict__ en dataclasses
    resp = joke.to_dict()
    return extract_joke(resp)


@mcp.tool
def tool_get_joke_by_id(joke_id: Annotated[int, Field(ge=1, le=451)]) -> str:
    """
    Retrieve a joke by its unique identifier using the repository.

    This function uses the Repository Pattern to fetch a specific joke by ID.
    The repository handles caching automatically, improving performance for
    repeated requests.

    :param joke_id: The unique identifier for the joke to be fetched (1-451).
    :type joke_id: Annotated[int, Field(ge=1, le=451)]
    :return: The content of the joke corresponding to the provided joke ID.
    :rtype: str
    """
    joke = joke_repo.get_joke_by_id(joke_id)
    # Evitar uso directo de __dict__ en dataclasses
    resp = joke.to_dict()
    return extract_joke(resp)


@mcp.tool
def tool_get_joke_by_type(joke_type: JOKE_TYPES) -> str:
    """
    Fetches a joke based on the specified joke type using the repository.

    This tool uses the Repository Pattern to retrieve jokes filtered by type.
    The repository provides caching and abstraction over the data source,
    making the code more maintainable and testable.

    :param joke_type: Type of joke to fetch (general, knock-knock, programming, dad).
    :type joke_type: JOKE_TYPES
    :return: A single joke string filtered by the specified joke type.
    :rtype: str
    """
    jokes = joke_repo.get_jokes_by_type(joke_type)
    # Evitar acceso a __dict__; usar métodos del modelo
    first_joke = jokes.get_jokes()[0]
    resp = first_joke.to_dict()

    return extract_joke(resp)


# --- Versiones asíncronas de las herramientas ---


@mcp.tool
async def tool_aget_joke() -> str:
    """
    Versión asíncrona: obtiene un chiste aleatorio usando el cliente HTTP async.

    :return: Chiste formateado "setup\npunchline".
    :rtype: str
    """
    joke = await api_aget_joke()
    return extract_joke(joke.to_dict())


@mcp.tool
async def tool_aget_joke_by_id(joke_id: Annotated[int, Field(ge=1, le=451)]) -> str:
    """
    Versión asíncrona: obtiene un chiste por ID usando el cliente HTTP async.
    """
    joke = await api_aget_joke_by_id(joke_id)
    return extract_joke(joke.to_dict())


@mcp.tool
async def tool_aget_joke_by_type(joke_type: JOKE_TYPES) -> str:
    """
    Versión asíncrona: obtiene chistes por tipo y devuelve el primero formateado.
    """
    jokes = await api_aget_jokes_by_type(joke_type)
    first = jokes.get_jokes()[0]
    return extract_joke(first.to_dict())


def run_server(
    transport_type: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    show_banner: bool = True,
) -> None:
    """
    Arranca el servidor MCP usando inyección de configuración.

    Si no se especifican parámetros, se consultan los valores por defecto
    desde Settings en el bloque de compatibilidad al final.
    """
    from strategies.factory import create_transport_strategy
    from utils.logger import log

    # Crear estrategia con DI (no leer Settings aquí)
    if transport_type is None:
        # Dejar que la capa de invocación decida los valores por defecto
        # pero aquí aseguramos un valor seguro (stdio) si nadie inyecta.
        transport_type = "stdio"

    strategy = create_transport_strategy(
        transport_type=transport_type,
        host=host,
        port=port,
        show_banner=show_banner,
    )

    # Preparar transporte
    strategy.prepare()

    # Obtener kwargs específicos del transporte
    transport_kwargs = strategy.get_transport_kwargs()

    log.info(f"Starting MCP server with {strategy.get_transport_name()} transport")
    log.debug(f"Transport configuration: {transport_kwargs}")

    # Ejecutar servidor
    mcp.run(**transport_kwargs)


if __name__ == "__main__":
    # Compatibilidad: leer Settings solo aquí y pasarlos por inyección
    from utils.config import Settings

    run_server(
        transport_type=Settings.MCP_PROTOCOL,
        host=Settings.MCP_SERVER_HOST,
        port=Settings.MCP_SERVER_PORT,
        show_banner=True,
    )
