"""
Joke API client module.

This module provides a clean interface for interacting with the joke API service,
implementing the Template Method pattern to reduce code duplication and ensure
consistent error handling across all API operations.
"""

import httpx
from typing import Annotated, TypeVar, Generic, Callable, Any
from pydantic import Field

from utils.model import Joke, Jokes
from utils.logger import log
from utils.constants import URL, JOKE_TYPES
from utils.exceptions import (
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
)

T = TypeVar('T', Joke, Jokes)


class JokeAPIClient:
    """
    Client for interacting with the Joke API service.

    This class implements the Template Method pattern, providing a unified
    interface for all API operations while eliminating code duplication.
    All HTTP request handling, error management, and response parsing
    is centralized in the _make_request method.

    :ivar base_url: The base URL for the joke API service
    :type base_url: str
    :ivar timeout: Request timeout in seconds
    :type timeout: float
    """

    def __init__(self, base_url: str = URL, timeout: float = 10.0):
        """
        Initialize the Joke API client.

        :param base_url: Base URL for the API service
        :param timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout

    def _make_request(
        self,
        endpoint: str,
        parser: Callable[[dict[str, Any]], T]
    ) -> T:
        """
        Template method for making HTTP requests to the API.

        This method implements the common logic for all API calls:
        1. Constructs the full URL
        2. Makes the HTTP GET request
        3. Handles connection and timeout errors
        4. Validates the response status code
        5. Parses the JSON response
        6. Returns the parsed result

        :param endpoint: API endpoint path (e.g., "/random_joke")
        :param parser: Function to parse the JSON response into the desired type
        :return: Parsed response object
        :raises JokeAPITimeoutError: If the request times out
        :raises JokeAPIConnectionError: If connection fails
        :raises JokeAPIHTTPError: If the API returns a non-200 status
        :raises JokeAPIParseError: If response parsing fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.get(url, timeout=self.timeout)
        except httpx.ReadTimeout as e:
            log.error(f"Timeout al conectar con {url}: {e}")
            raise JokeAPITimeoutError()
        except httpx.ConnectError as e:
            log.error(f"Error de conexión con {url}: {e}")
            raise JokeAPIConnectionError()
        except httpx.HTTPError as e:
            log.error(f"Error HTTP inesperado en {url}: {e}")
            raise JokeAPIConnectionError(f"Error HTTP inesperado: {e}")

        if response.status_code != 200:
            log.error(f"Error {response.status_code} al obtener {url}: {response.text}")
            raise JokeAPIHTTPError(
                message="Error al obtener información del servicio de Jokes",
                status_code=response.status_code,
                response_text=response.text
            )

        try:
            response_data = response.json()
            return parser(response_data)
        except (ValueError, TypeError, KeyError) as e:
            log.error(f"Error al parsear respuesta de {url}: {e}")
            raise JokeAPIParseError(f"Error al parsear la respuesta: {e}")

    def get_joke(self) -> Joke:
        """
        Fetch a random joke from the joke service.

        :return: A random joke
        :rtype: Joke
        :raises JokeAPITimeoutError: If the request times out
        :raises JokeAPIConnectionError: If connection fails
        :raises JokeAPIHTTPError: If the API returns an error status
        :raises JokeAPIParseError: If response parsing fails
        """
        return self._make_request("/random_joke", lambda data: Joke(**data))

    def get_ten_jokes(self) -> Jokes:
        """
        Fetch ten random jokes from the joke service.

        :return: A collection of ten jokes
        :rtype: Jokes
        :raises JokeAPITimeoutError: If the request times out
        :raises JokeAPIConnectionError: If connection fails
        :raises JokeAPIHTTPError: If the API returns an error status
        :raises JokeAPIParseError: If response parsing fails
        """
        return self._make_request("/random_ten", lambda data: Jokes(jokes=data))

    def get_joke_by_id(self, joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
        """
        Fetch a specific joke by its ID.

        :param joke_id: The ID of the joke to fetch (must be between 1 and 451)
        :type joke_id: int
        :return: The requested joke
        :rtype: Joke
        :raises JokeAPITimeoutError: If the request times out
        :raises JokeAPIConnectionError: If connection fails
        :raises JokeAPIHTTPError: If the API returns an error status
        :raises JokeAPIParseError: If response parsing fails
        """
        return self._make_request(f"/jokes/{joke_id}", lambda data: Joke(**data))

    def get_jokes_by_type(self, joke_type: JOKE_TYPES) -> Jokes:
        """
        Fetch a random joke of a specific type.

        :param joke_type: The type of joke to fetch (general, knock-knock, programming, or dad)
        :type joke_type: JOKE_TYPES
        :return: A joke of the specified type
        :rtype: Jokes
        :raises JokeAPITimeoutError: If the request times out
        :raises JokeAPIConnectionError: If connection fails
        :raises JokeAPIHTTPError: If the API returns an error status
        :raises JokeAPIParseError: If response parsing fails
        """
        return self._make_request(f"/jokes/{joke_type}/random", lambda data: Jokes(jokes=data))


# Singleton instance for convenience
_client = JokeAPIClient()


# Convenience functions that maintain backward compatibility
def get_joke() -> Joke:
    """
    Fetch a random joke from the joke service.

    This is a convenience function that uses the singleton JokeAPIClient instance.

    :return: A random joke
    :rtype: Joke
    :raises JokeAPITimeoutError: If the request times out
    :raises JokeAPIConnectionError: If connection fails
    :raises JokeAPIHTTPError: If the API returns an error status
    :raises JokeAPIParseError: If response parsing fails
    """
    return _client.get_joke()


def get_ten_jokes() -> Jokes:
    """
    Fetch ten random jokes from the joke service.

    This is a convenience function that uses the singleton JokeAPIClient instance.

    :return: A collection of ten jokes
    :rtype: Jokes
    :raises JokeAPITimeoutError: If the request times out
    :raises JokeAPIConnectionError: If connection fails
    :raises JokeAPIHTTPError: If the API returns an error status
    :raises JokeAPIParseError: If response parsing fails
    """
    return _client.get_ten_jokes()


def get_joke_by_id(joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
    """
    Fetch a specific joke by its ID.

    This is a convenience function that uses the singleton JokeAPIClient instance.

    :param joke_id: The ID of the joke to fetch (must be between 1 and 451)
    :type joke_id: int
    :return: The requested joke
    :rtype: Joke
    :raises JokeAPITimeoutError: If the request times out
    :raises JokeAPIConnectionError: If connection fails
    :raises JokeAPIHTTPError: If the API returns an error status
    :raises JokeAPIParseError: If response parsing fails
    """
    return _client.get_joke_by_id(joke_id)


def get_jokes_by_type(joke_type: JOKE_TYPES) -> Jokes:
    """
    Fetch a random joke of a specific type.

    This is a convenience function that uses the singleton JokeAPIClient instance.

    :param joke_type: The type of joke to fetch (general, knock-knock, programming, or dad)
    :type joke_type: JOKE_TYPES
    :return: A joke of the specified type
    :rtype: Jokes
    :raises JokeAPITimeoutError: If the request times out
    :raises JokeAPIConnectionError: If connection fails
    :raises JokeAPIHTTPError: If the API returns an error status
    :raises JokeAPIParseError: If response parsing fails
    """
    return _client.get_jokes_by_type(joke_type)
