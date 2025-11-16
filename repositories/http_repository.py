"""
HTTP-based joke repository implementation.

This module provides a concrete implementation of the JokeRepository interface
that fetches jokes from an external HTTP API using the JokeAPIClient.
"""

from typing import Annotated
from pydantic import Field

from repositories.base import JokeRepository, JokeRepositoryError, JokeNotFoundError
from utils.model import Joke, Jokes
from utils.constants import JOKE_TYPES, joke_type_value
from utils.RequestAPIJokes import JokeAPIClient
from utils.exceptions import (
    JokeAPIError,
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
)
from utils.logger import log


class HTTPJokeRepository(JokeRepository):
    """
    Repository implementation that fetches jokes from an HTTP API.

    This class implements the JokeRepository interface using an HTTP client
    to communicate with an external joke API service. It translates API-specific
    exceptions into repository-level exceptions for better abstraction.

    :ivar _client: The HTTP client used to communicate with the API
    :type _client: JokeAPIClient
    """

    def __init__(self, client: JokeAPIClient | None = None):
        """
        Initialize the HTTP joke repository.

        :param client: Optional JokeAPIClient instance. If not provided,
                       a new client will be created with default settings.
        :type client: JokeAPIClient | None
        """
        self._client = client or JokeAPIClient()
        log.info(f"HTTPJokeRepository initialized with base_url: {self._client.base_url}")

    def get_random_joke(self) -> Joke:
        """
        Retrieve a random joke from the HTTP API.

        :return: A random joke
        :rtype: Joke
        :raises JokeRepositoryError: If the operation fails
        """
        try:
            log.debug("Fetching random joke from HTTP API")
            joke = self._client.get_joke()
            log.debug(f"Successfully fetched joke ID: {joke.id}")
            return joke
        except JokeAPIError as e:
            log.error(f"Failed to fetch random joke: {e}")
            raise JokeRepositoryError(
                "Failed to retrieve random joke from repository",
                cause=e
            )

    def get_random_jokes(self, count: int = 10) -> Jokes:
        """
        Retrieve multiple random jokes from the HTTP API.

        Note: The current API implementation always returns 10 jokes,
        regardless of the count parameter.

        :param count: Number of jokes to retrieve (currently ignored by API)
        :type count: int
        :return: A collection of random jokes
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        try:
            log.debug(f"Fetching {count} random jokes from HTTP API")
            jokes = self._client.get_ten_jokes()
            log.debug(f"Successfully fetched {len(jokes.jokes)} jokes")
            return jokes
        except JokeAPIError as e:
            log.error(f"Failed to fetch random jokes: {e}")
            raise JokeRepositoryError(
                f"Failed to retrieve {count} random jokes from repository",
                cause=e
            )

    def get_joke_by_id(self, joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
        """
        Retrieve a specific joke by its ID from the HTTP API.

        :param joke_id: The ID of the joke to retrieve (1-451)
        :type joke_id: int
        :return: The requested joke
        :rtype: Joke
        :raises JokeNotFoundError: If the joke doesn't exist
        :raises JokeRepositoryError: If the operation fails for other reasons
        """
        try:
            log.debug(f"Fetching joke by ID: {joke_id}")
            joke = self._client.get_joke_by_id(joke_id)
            log.debug(f"Successfully fetched joke ID: {joke.id}")
            return joke
        except JokeAPIHTTPError as e:
            # If we get a 404, translate it to JokeNotFoundError
            if e.status_code == 404:
                log.warning(f"Joke with ID {joke_id} not found")
                raise JokeNotFoundError(joke_id)
            log.error(f"HTTP error fetching joke {joke_id}: {e}")
            raise JokeRepositoryError(
                f"Failed to retrieve joke with ID {joke_id}",
                cause=e
            )
        except JokeAPIError as e:
            log.error(f"Failed to fetch joke {joke_id}: {e}")
            raise JokeRepositoryError(
                f"Failed to retrieve joke with ID {joke_id}",
                cause=e
            )

    def get_jokes_by_type(self, joke_type: JOKE_TYPES) -> Jokes:
        """
        Retrieve jokes of a specific type from the HTTP API.

        :param joke_type: The type of jokes to retrieve
        :type joke_type: JOKE_TYPES
        :return: A collection of jokes of the specified type
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        try:
            jt = joke_type_value(joke_type)
            log.debug(f"Fetching jokes of type: {jt}")
            jokes = self._client.get_jokes_by_type(joke_type)
            log.debug(f"Successfully fetched {len(jokes.jokes)} jokes of type {jt}")
            return jokes
        except JokeAPIError as e:
            jt = joke_type_value(joke_type)
            log.error(f"Failed to fetch jokes of type {jt}: {e}")
            raise JokeRepositoryError(
                f"Failed to retrieve jokes of type '{jt}' from repository",
                cause=e
            )

    def health_check(self) -> bool:
        """
        Check if the HTTP API is accessible and healthy.

        This performs a lightweight operation (fetching a single joke)
        to verify connectivity and service availability.

        :return: True if healthy, False otherwise
        :rtype: bool
        """
        try:
            log.debug("Performing health check on HTTP API")
            self._client.get_joke()
            log.info("Health check passed - HTTP API is accessible")
            return True
        except (JokeAPITimeoutError, JokeAPIConnectionError) as e:
            log.warning(f"Health check failed - API is not accessible: {e}")
            return False
        except JokeAPIError as e:
            log.warning(f"Health check failed with error: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error during health check: {e}")
            return False

    def __repr__(self) -> str:
        """
        Return a string representation of the repository.

        :return: String representation
        :rtype: str
        """
        return f"HTTPJokeRepository(base_url={self._client.base_url!r})"
