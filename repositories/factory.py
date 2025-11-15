"""
Repository factory for creating joke repository instances.

This module implements the Factory Pattern to create and configure
joke repository instances based on configuration settings.
"""

from typing import Literal
from enum import Enum

from repositories.base import JokeRepository
from repositories.http_repository import HTTPJokeRepository
from repositories.cached_repository import CachedJokeRepository
from utils.RequestAPIJokes import JokeAPIClient
from utils.config import Settings
from utils.logger import log


class RepositoryType(str, Enum):
    """
    Enumeration of available repository types.

    This enum defines the different types of repositories that can be created.
    """

    HTTP = "http"
    CACHED = "cached"


class RepositoryFactory:
    """
    Factory for creating joke repository instances.

    This class implements the Factory Pattern, providing methods to create
    different types of joke repositories with appropriate configuration.
    It encapsulates the complexity of repository creation and configuration.

    Benefits:
    - Centralized repository creation logic
    - Easy to switch between repository types
    - Configuration-driven repository selection
    - Supports different deployment scenarios (dev, test, prod)
    """

    @staticmethod
    def create_http_repository(
        base_url: str | None = None,
        timeout: float = 10.0
    ) -> HTTPJokeRepository:
        """
        Create an HTTP-based joke repository.

        :param base_url: Optional custom base URL (uses Settings.API_BASE_URL if not provided)
        :type base_url: str | None
        :param timeout: Request timeout in seconds
        :type timeout: float
        :return: Configured HTTP repository
        :rtype: HTTPJokeRepository
        """
        api_url = base_url or Settings.API_BASE_URL
        client = JokeAPIClient(base_url=api_url, timeout=timeout)
        repository = HTTPJokeRepository(client=client)

        log.info(f"Created HTTPJokeRepository with URL: {api_url}")
        return repository

    @staticmethod
    def create_cached_repository(
        base_repository: JokeRepository | None = None,
        cache_ttl: int = 300
    ) -> CachedJokeRepository:
        """
        Create a cached joke repository.

        This wraps an existing repository (or creates an HTTP one) with caching.

        :param base_repository: Optional base repository to wrap (creates HTTP if not provided)
        :type base_repository: JokeRepository | None
        :param cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        :type cache_ttl: int
        :return: Cached repository
        :rtype: CachedJokeRepository
        """
        # If no base repository provided, create an HTTP one
        if base_repository is None:
            base_repository = RepositoryFactory.create_http_repository()

        cached_repo = CachedJokeRepository(
            repository=base_repository,
            default_ttl=cache_ttl
        )

        log.info(f"Created CachedJokeRepository with TTL: {cache_ttl}s")
        return cached_repo

    @staticmethod
    def create_repository(
        repository_type: RepositoryType | str = RepositoryType.CACHED,
        **kwargs
    ) -> JokeRepository:
        """
        Create a repository based on the specified type.

        This is the main factory method that creates repositories based on type.

        :param repository_type: Type of repository to create
        :type repository_type: RepositoryType | str
        :param kwargs: Additional keyword arguments passed to specific factory methods
        :return: Configured repository instance
        :rtype: JokeRepository
        :raises ValueError: If repository_type is not recognized
        """
        # Convert string to enum if necessary
        if isinstance(repository_type, str):
            try:
                repository_type = RepositoryType(repository_type.lower())
            except ValueError:
                valid_types = [t.value for t in RepositoryType]
                raise ValueError(
                    f"Invalid repository type: {repository_type}. "
                    f"Valid types are: {valid_types}"
                )

        log.info(f"Creating repository of type: {repository_type.value}")

        if repository_type == RepositoryType.HTTP:
            return RepositoryFactory.create_http_repository(**kwargs)
        elif repository_type == RepositoryType.CACHED:
            return RepositoryFactory.create_cached_repository(**kwargs)
        else:
            raise ValueError(f"Unsupported repository type: {repository_type}")


# Singleton instance for the default repository
_default_repository: JokeRepository | None = None


def get_joke_repository(
    force_recreate: bool = False,
    repository_type: RepositoryType | str = RepositoryType.CACHED,
    **kwargs
) -> JokeRepository:
    """
    Get the default joke repository instance (singleton).

    This function provides a convenient way to get a repository instance
    without having to manually create one each time. It maintains a singleton
    instance that is reused across calls.

    :param force_recreate: If True, force creation of a new repository
    :type force_recreate: bool
    :param repository_type: Type of repository to create (if creating new)
    :type repository_type: RepositoryType | str
    :param kwargs: Additional arguments passed to the factory
    :return: Repository instance
    :rtype: JokeRepository

    Example:
        # Get default cached repository
        repo = get_joke_repository()

        # Force create a new HTTP-only repository
        repo = get_joke_repository(force_recreate=True, repository_type="http")
    """
    global _default_repository

    if _default_repository is None or force_recreate:
        _default_repository = RepositoryFactory.create_repository(
            repository_type=repository_type,
            **kwargs
        )
        log.info("Default joke repository initialized")

    return _default_repository


def reset_repository():
    """
    Reset the default repository singleton.

    Useful for testing to ensure a clean state.
    """
    global _default_repository
    _default_repository = None
    log.debug("Default repository reset")
