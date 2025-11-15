"""
Repository pattern implementations for data access.

This package provides repository interfaces and implementations following
the Repository Pattern, which abstracts data access and provides a
collection-like interface for domain objects.
"""

from repositories.base import (
    JokeRepository,
    JokeRepositoryError,
    JokeNotFoundError,
)
from repositories.http_repository import HTTPJokeRepository
from repositories.cached_repository import CachedJokeRepository
from repositories.factory import RepositoryFactory, get_joke_repository, reset_repository

__all__ = [
    # Base interfaces and exceptions
    'JokeRepository',
    'JokeRepositoryError',
    'JokeNotFoundError',
    # Implementations
    'HTTPJokeRepository',
    'CachedJokeRepository',
    # Factory
    'RepositoryFactory',
    'get_joke_repository',
    'reset_repository',
]
