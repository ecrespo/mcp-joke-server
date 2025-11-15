"""
Base repository interfaces and abstract classes.

This module defines the repository pattern interfaces for data access abstraction.
Repositories provide a collection-like interface for accessing domain objects,
decoupling business logic from data access implementation details.
"""

from abc import ABC, abstractmethod
from typing import Annotated
from pydantic import Field

from utils.model import Joke, Jokes
from utils.constants import JOKE_TYPES


class JokeRepository(ABC):
    """
    Abstract base class for joke repositories.

    This interface defines the contract for accessing joke data,
    allowing different implementations (HTTP API, database, cache, mock, etc.)
    without changing the business logic.

    The Repository Pattern provides:
    - Abstraction over data sources
    - Centralized data access logic
    - Easy testing with mock implementations
    - Flexibility to change data sources
    """

    @abstractmethod
    def get_random_joke(self) -> Joke:
        """
        Retrieve a random joke.

        :return: A random joke
        :rtype: Joke
        :raises JokeRepositoryError: If the operation fails
        """
        pass

    @abstractmethod
    def get_random_jokes(self, count: int = 10) -> Jokes:
        """
        Retrieve multiple random jokes.

        :param count: Number of jokes to retrieve
        :type count: int
        :return: A collection of random jokes
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        pass

    @abstractmethod
    def get_joke_by_id(self, joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
        """
        Retrieve a specific joke by its ID.

        :param joke_id: The ID of the joke to retrieve
        :type joke_id: int
        :return: The requested joke
        :rtype: Joke
        :raises JokeRepositoryError: If the operation fails
        :raises JokeNotFoundError: If the joke doesn't exist
        """
        pass

    @abstractmethod
    def get_jokes_by_type(self, joke_type: JOKE_TYPES) -> Jokes:
        """
        Retrieve jokes of a specific type.

        :param joke_type: The type of jokes to retrieve
        :type joke_type: JOKE_TYPES
        :return: A collection of jokes of the specified type
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the repository is healthy and accessible.

        :return: True if healthy, False otherwise
        :rtype: bool
        """
        pass


class JokeRepositoryError(Exception):
    """
    Base exception for repository errors.

    This exception should be raised by repository implementations
    when data access operations fail.
    """

    def __init__(self, message: str, cause: Exception | None = None):
        """
        Initialize the repository error.

        :param message: Error message
        :param cause: Original exception that caused this error
        """
        super().__init__(message)
        self.cause = cause


class JokeNotFoundError(JokeRepositoryError):
    """
    Exception raised when a requested joke is not found.

    This specific exception allows clients to distinguish between
    "joke doesn't exist" and other types of errors.
    """

    def __init__(self, joke_id: int):
        """
        Initialize the not found error.

        :param joke_id: ID of the joke that wasn't found
        """
        super().__init__(f"Joke with ID {joke_id} not found")
        self.joke_id = joke_id
