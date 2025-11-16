"""
Unit tests for repositories/cached_repository.py

Tests for the cached repository decorator pattern implementation.
"""

import time
from datetime import datetime

import pytest

from repositories.base import JokeNotFoundError
from repositories.cached_repository import CachedJokeRepository, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_create_cache_entry(self, sample_joke):
        """Test creating a cache entry."""
        entry = CacheEntry(sample_joke, ttl_seconds=300)
        assert entry.value == sample_joke
        assert isinstance(entry.expires_at, datetime)

    def test_cache_entry_not_expired_immediately(self, sample_joke):
        """Test that newly created entry is not expired."""
        entry = CacheEntry(sample_joke, ttl_seconds=10)
        assert not entry.is_expired()

    def test_cache_entry_expires(self, sample_joke):
        """Test that cache entry expires after TTL."""
        entry = CacheEntry(sample_joke, ttl_seconds=0)
        time.sleep(0.1)  # Wait a bit
        assert entry.is_expired()


class TestCachedJokeRepository:
    """Tests for CachedJokeRepository decorator."""

    def test_initialization(self, mock_repository):
        """Test cached repository initialization."""
        cached_repo = CachedJokeRepository(mock_repository, default_ttl=300)
        assert cached_repo._repository is mock_repository
        assert cached_repo._default_ttl == 300
        assert len(cached_repo._cache) == 0

    def test_get_random_joke_not_cached(self, mock_repository):
        """Test that random jokes are not cached."""
        cached_repo = CachedJokeRepository(mock_repository)

        joke1 = cached_repo.get_random_joke()
        joke2 = cached_repo.get_random_joke()

        # Should call wrapped repository each time
        assert mock_repository.calls["get_random_joke"] == 2
        assert len(cached_repo._cache) == 0  # No cache for random

    def test_get_random_jokes_not_cached(self, mock_repository):
        """Test that random jokes collection is not cached."""
        cached_repo = CachedJokeRepository(mock_repository)

        jokes1 = cached_repo.get_random_jokes(10)
        jokes2 = cached_repo.get_random_jokes(10)

        # Should call wrapped repository each time
        assert mock_repository.calls["get_random_jokes"] == 2
        assert len(cached_repo._cache) == 0

    def test_get_joke_by_id_caches(self, mock_repository):
        """Test that get_joke_by_id uses cache."""
        cached_repo = CachedJokeRepository(mock_repository)

        # First call - cache miss
        joke1 = cached_repo.get_joke_by_id(1)
        assert mock_repository.calls["get_joke_by_id"] == 1
        assert len(cached_repo._cache) == 1

        # Second call - cache hit
        joke2 = cached_repo.get_joke_by_id(1)
        assert mock_repository.calls["get_joke_by_id"] == 1  # No additional call
        assert joke1 is joke2  # Same object from cache

    def test_get_joke_by_id_different_ids(self, mock_repository):
        """Test caching different joke IDs."""
        cached_repo = CachedJokeRepository(mock_repository)

        joke1 = cached_repo.get_joke_by_id(1)
        joke2 = cached_repo.get_joke_by_id(2)
        joke3 = cached_repo.get_joke_by_id(3)

        assert mock_repository.calls["get_joke_by_id"] == 3
        assert len(cached_repo._cache) == 3

        # Access cached jokes
        joke1_cached = cached_repo.get_joke_by_id(1)
        assert joke1 is joke1_cached
        assert mock_repository.calls["get_joke_by_id"] == 3  # No new calls

    def test_get_jokes_by_type_caches(self, mock_repository):
        """Test that get_jokes_by_type uses cache."""
        cached_repo = CachedJokeRepository(mock_repository)

        # First call - cache miss
        jokes1 = cached_repo.get_jokes_by_type("programming")
        assert mock_repository.calls["get_jokes_by_type"] == 1
        assert len(cached_repo._cache) == 1

        # Second call - cache hit
        jokes2 = cached_repo.get_jokes_by_type("programming")
        assert mock_repository.calls["get_jokes_by_type"] == 1
        assert jokes1 is jokes2

    def test_get_jokes_by_type_different_types(self, mock_repository):
        """Test caching different joke types."""
        cached_repo = CachedJokeRepository(mock_repository)

        prog_jokes = cached_repo.get_jokes_by_type("programming")
        gen_jokes = cached_repo.get_jokes_by_type("general")

        assert mock_repository.calls["get_jokes_by_type"] == 2
        assert len(cached_repo._cache) == 2

    def test_cache_stats_initial(self, mock_repository):
        """Test initial cache statistics."""
        cached_repo = CachedJokeRepository(mock_repository)
        stats = cached_repo.get_cache_stats()

        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["total_requests"] == 0
        assert stats["hit_rate_percent"] == 0.0
        assert stats["cache_size"] == 0

    def test_cache_stats_after_operations(self, mock_repository):
        """Test cache statistics after some operations."""
        cached_repo = CachedJokeRepository(mock_repository)

        # Cache miss
        cached_repo.get_joke_by_id(1)
        # Cache hit
        cached_repo.get_joke_by_id(1)
        # Cache miss
        cached_repo.get_joke_by_id(2)

        stats = cached_repo.get_cache_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["total_requests"] == 3
        assert stats["hit_rate_percent"] == pytest.approx(33.33, rel=0.1)
        assert stats["cache_size"] == 2

    def test_clear_cache(self, mock_repository):
        """Test clearing the cache."""
        cached_repo = CachedJokeRepository(mock_repository)

        # Populate cache
        cached_repo.get_joke_by_id(1)
        cached_repo.get_joke_by_id(2)
        assert len(cached_repo._cache) == 2

        # Clear cache
        cached_repo.clear_cache()
        assert len(cached_repo._cache) == 0

        # Verify stats are preserved
        stats = cached_repo.get_cache_stats()
        assert stats["misses"] == 2  # Stats not reset

    def test_health_check_delegates(self, mock_repository):
        """Test that health_check delegates to wrapped repository."""
        cached_repo = CachedJokeRepository(mock_repository)

        result = cached_repo.health_check()
        assert result is True
        assert mock_repository.calls["health_check"] == 1

    def test_cache_expiration(self, mock_repository):
        """Test that cache entries expire after TTL."""
        cached_repo = CachedJokeRepository(mock_repository, default_ttl=1)

        # First call - cache miss
        joke1 = cached_repo.get_joke_by_id(1)
        assert mock_repository.calls["get_joke_by_id"] == 1

        # Wait for expiration
        time.sleep(1.1)

        # Second call - cache expired, should fetch again
        joke2 = cached_repo.get_joke_by_id(1)
        assert mock_repository.calls["get_joke_by_id"] == 2

        stats = cached_repo.get_cache_stats()
        assert stats["evictions"] == 1  # One entry evicted

    def test_joke_not_found_propagates(self, mock_repository):
        """Test that JokeNotFoundError propagates through cache."""
        cached_repo = CachedJokeRepository(mock_repository)

        with pytest.raises(JokeNotFoundError) as exc_info:
            cached_repo.get_joke_by_id(999)

        assert exc_info.value.joke_id == 999

    def test_repr(self, mock_repository):
        """Test string representation."""
        cached_repo = CachedJokeRepository(mock_repository, default_ttl=600)
        repr_str = repr(cached_repo)

        assert "CachedJokeRepository" in repr_str
        assert "600" in repr_str  # TTL
        assert "hit_rate" in repr_str
