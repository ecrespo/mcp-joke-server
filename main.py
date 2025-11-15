from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from utils.constants import CONSISTENT_JOKE, JOKE_TYPES
from utils.formatters import extract_joke
from utils.RequestAPIJokes import (
    get_joke,
    get_jokes_by_type,
    get_joke_by_id
)
mcp = FastMCP("jokes (python)")



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
def tool_get_joke()-> str:
    """
    Fetches a joke from an external joke provider using its API and extracts the relevant
    text content of the joke.

    This function serves as an interface to interact with an underlying joke API. It retrieves
    raw data, processes it, and extracts a structured joke string for further consumption.

    :return: A string containing the extracted joke.
    :rtype: str
    """
    joke = get_joke()
    resp = joke.__dict__
    return extract_joke(resp)


@mcp.tool
def tool_get_joke_by_id(joke_id: Annotated[int, Field(ge=1, le=451)]) -> str:
    """
    Retrieve a joke by its unique identifier.

    This function processes the given joke ID, fetches the appropriate joke
    data, and extracts the relevant joke content to return. It ensures
    that the joke ID falls within the specified range of valid values.

    :param joke_id: The unique identifier for the joke to be fetched.
    :type joke_id: Annotated[int, Field(ge=1, le=451)]
    :return: The content of the joke corresponding to the provided joke ID.
    :rtype: str
    """
    joke = get_joke_by_id(joke_id)
    resp = joke.__dict__
    return extract_joke(resp)


@mcp.tool
def tool_get_joke_by_type(joke_type: JOKE_TYPES) -> str:
    """
    Fetches a joke based on the specified joke type.

    This tool retrieves a joke of a particular type from a predefined dataset or API.
    The function ensures that jokes are filtered based on their type and then properly
    processed to extract only the relevant joke content. The result is returned
    as a string that represents a single joke.

    :param joke_type: Type of joke to fetch.
    :type joke_type: JOKE_TYPES
    :return: A single joke string filtered by the specified joke type.
    :rtype: str
    """
    jokes = get_jokes_by_type(joke_type)
    resp = jokes.__dict__['jokes'][0].__dict__

    return extract_joke(resp)



if __name__ == "__main__":
    mcp.run()
