"""
Cached joke repository implementation using Decorator pattern.

This module provides a caching decorator for joke repositories, adding
in-memory caching capabilities to any JokeRepository implementation.
"""

from typing import Annotated
from datetime import datetime, timedelta
from pydantic import Field

from repositories.base import JokeRepository, JokeRepositoryError, JokeNotFoundError
from utils.model import Joke, Jokes
from utils.constants import JOKE_TYPES, joke_type_value
from utils.logger import setup_logger
from utils.logging_interfaces import LoggerProtocol


class CacheEntry:
    """
    Represents a single cache entry with expiration support.

    :ivar value: The cached value
    :ivar expires_at: Timestamp when this entry expires
    """

    def __init__(self, value: Joke | Jokes, ttl_seconds: int):
        """
        Initialize a cache entry.

        :param value: The value to cache
        :param ttl_seconds: Time-to-live in seconds
        """
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """
        Check if this cache entry has expired.

        :return: True if expired, False otherwise
        """
        return datetime.now() > self.expires_at


class CachedJokeRepository(JokeRepository):
    """
    Repository decorator that adds caching capabilities.

    This class implements the Decorator Pattern, wrapping any JokeRepository
    implementation and adding an in-memory cache layer. It maintains cache
    entries with configurable time-to-live (TTL) and provides cache statistics.

    Benefits:
    - Reduces API calls
    - Improves response time for repeated queries
    - Configurable TTL per cache entry
    - Transparent to clients (same interface)
    - Can wrap any repository implementation

    :ivar _repository: The wrapped repository
    :ivar _cache: In-memory cache dictionary
    :ivar _default_ttl: Default time-to-live for cache entries in seconds
    :ivar _stats: Cache statistics
    """

    def __init__(self, repository: JokeRepository, default_ttl: int = 300, *, logger: LoggerProtocol | None = None):
        """
        Initialize the cached repository.

        :param repository: The repository to wrap with caching
        :type repository: JokeRepository
        :param default_ttl: Default cache TTL in seconds (default: 300 = 5 minutes)
        :type default_ttl: int
        """
        self._repository = repository
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
        }
        self._log: LoggerProtocol = logger or setup_logger()
        self._log.info(
            f"CachedJokeRepository initialized with TTL={default_ttl}s, "
            f"wrapping {type(repository).__name__}"
        )

    def _get_from_cache(self, key: str) -> Joke | Jokes | None:
        """
        Retrieve a value from cache if it exists and is not expired.

        :param key: Cache key
        :return: Cached value or None if not found or expired
        """
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                self._stats['hits'] += 1
                self._log.debug(f"Cache HIT for key: {key}")
                return entry.value
            else:
                # Entry expired, remove it
                del self._cache[key]
                self._stats['evictions'] += 1
                self._log.debug(f"Cache entry expired and evicted: {key}")

        self._stats['misses'] += 1
        self._log.debug(f"Cache MISS for key: {key}")
        return None

    def _put_in_cache(self, key: str, value: Joke | Jokes, ttl: int | None = None):
        """
        Store a value in cache with optional TTL.

        :param key: Cache key
        :param value: Value to cache
        :param ttl: Optional TTL override (uses default if not provided)
        """
        ttl = ttl or self._default_ttl
        self._cache[key] = CacheEntry(value, ttl)
        self._log.debug(f"Cached value for key: {key} (TTL={ttl}s)")

    def _clear_expired(self):
        """
        Remove all expired entries from the cache.

        This is called periodically to prevent memory bloat.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
            self._stats['evictions'] += 1

        if expired_keys:
            self._log.debug(f"Cleared {len(expired_keys)} expired cache entries")

    def get_random_joke(self) -> Joke:
        """
        Retrieve a random joke.

        Note: Random jokes are not cached as they should be different each time.

        :return: A random joke
        :rtype: Joke
        :raises JokeRepositoryError: If the operation fails
        """
        # Don't cache random jokes - they should be random!
        self._log.debug("Fetching random joke (not cached)")
        return self._repository.get_random_joke()

    def get_random_jokes(self, count: int = 10) -> Jokes:
        """
        Retrieve multiple random jokes.

        Note: Random jokes are not cached as they should be different each time.

        :param count: Number of jokes to retrieve
        :type count: int
        :return: A collection of random jokes
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        # Don't cache random jokes - they should be random!
        self._log.debug(f"Fetching {count} random jokes (not cached)")
        return self._repository.get_random_jokes(count)

    def get_joke_by_id(self, joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
        """
        Retrieve a specific joke by its ID, using cache if available.

        Jokes are cached by ID since they don't change.

        :param joke_id: The ID of the joke to retrieve
        :type joke_id: int
        :return: The requested joke
        :rtype: Joke
        :raises JokeNotFoundError: If the joke doesn't exist
        :raises JokeRepositoryError: If the operation fails
        """
        cache_key = f"joke:{joke_id}"

        # Try to get from cache
        cached_joke = self._get_from_cache(cache_key)
        if cached_joke is not None:
            return cached_joke

        # Cache miss - fetch from wrapped repository
        self._log.debug(f"Fetching joke {joke_id} from repository")
        joke = self._repository.get_joke_by_id(joke_id)

        # Cache the result
        self._put_in_cache(cache_key, joke)

        return joke

    def get_jokes_by_type(self, joke_type: JOKE_TYPES) -> Jokes:
        """
        Retrieve jokes of a specific type, using cache if available.

        :param joke_type: The type of jokes to retrieve
        :type joke_type: JOKE_TYPES
        :return: A collection of jokes of the specified type
        :rtype: Jokes
        :raises JokeRepositoryError: If the operation fails
        """
        jt = joke_type_value(joke_type)
        cache_key = f"jokes:type:{jt}"

        # Try to get from cache
        cached_jokes = self._get_from_cache(cache_key)
        if cached_jokes is not None:
            return cached_jokes

        # Cache miss - fetch from wrapped repository
        self._log.debug(f"Fetching jokes of type {jt} from repository")
        jokes = self._repository.get_jokes_by_type(joke_type)

        # Cache the result
        self._put_in_cache(cache_key, jokes)

        return jokes

    def health_check(self) -> bool:
        """
        Check if the underlying repository is healthy.

        This delegates to the wrapped repository without caching.

        :return: True if healthy, False otherwise
        :rtype: bool
        """
        return self._repository.health_check()

    def clear_cache(self):
        """
        Clear all entries from the cache.

        Useful for testing or when fresh data is required.
        """
        cache_size = len(self._cache)
        self._cache.clear()
        self._log.info(f"Cache cleared - removed {cache_size} entries")

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        :return: Dictionary with cache hits, misses, and evictions
        :rtype: dict[str, int]
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (
            self._stats['hits'] / total_requests * 100
            if total_requests > 0
            else 0.0
        )

        return {
            **self._stats,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'cache_size': len(self._cache),
        }

    def __repr__(self) -> str:
        """
        Return a string representation of the cached repository.

        :return: String representation
        :rtype: str
        """
        stats = self.get_cache_stats()
        return (
            f"CachedJokeRepository("
            f"repository={self._repository!r}, "
            f"ttl={self._default_ttl}s, "
            f"cache_size={stats['cache_size']}, "
            f"hit_rate={stats['hit_rate_percent']}%"
            f")"
        )
