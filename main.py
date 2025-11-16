"""
MCP Joke Server - Main application module.

This module implements the FastMCP server with tools for fetching jokes
using the Repository Pattern for data access abstraction.
"""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from utils.constants import CONSISTENT_JOKE, JOKE_TYPES
from utils.formatters import extract_joke
from repositories import get_joke_repository

# Initialize MCP server
mcp = FastMCP("jokes (python)")

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



if __name__ == "__main__":
    from utils.config import Settings
    protocol_mmcp = Settings.PROTOCOL_MCP
    if protocol_mmcp == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport="streamable-http",
            host=Settings.MCP_SERVER_HOST,
            port=Settings.MCP_SERVER_PORT
        )
