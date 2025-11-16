"""
Unit tests for repositories/factory.py

Tests for repository factory and singleton pattern.
"""

import pytest

from repositories.cached_repository import CachedJokeRepository
from repositories.factory import (
    RepositoryFactory,
    RepositoryType,
    get_joke_repository,
    reset_repository,
)
from repositories.http_repository import HTTPJokeRepository


class TestRepositoryType:
    """Tests for RepositoryType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert RepositoryType.HTTP.value == "http"
        assert RepositoryType.CACHED.value == "cached"

    def test_string_values(self):
        """Test that enum values are strings."""
        assert isinstance(RepositoryType.HTTP, str)
        assert isinstance(RepositoryType.CACHED, str)


class TestRepositoryFactory:
    """Tests for RepositoryFactory class."""

    def test_create_http_repository(self):
        """Test creating HTTP repository."""
        repo = RepositoryFactory.create_http_repository()
        assert isinstance(repo, HTTPJokeRepository)

    def test_create_http_repository_with_custom_url(self):
        """Test creating HTTP repository with custom URL."""
        repo = RepositoryFactory.create_http_repository(
            base_url="https://example.com", timeout=15.0
        )
        assert isinstance(repo, HTTPJokeRepository)
        assert repo._client.base_url == "https://example.com"
        assert repo._client.timeout == 15.0

    def test_create_cached_repository(self):
        """Test creating cached repository."""
        repo = RepositoryFactory.create_cached_repository()
        assert isinstance(repo, CachedJokeRepository)

    def test_create_cached_repository_with_custom_ttl(self):
        """Test creating cached repository with custom TTL."""
        repo = RepositoryFactory.create_cached_repository(cache_ttl=600)
        assert isinstance(repo, CachedJokeRepository)
        assert repo._default_ttl == 600

    def test_create_cached_repository_with_base_repo(self, mock_repository):
        """Test creating cached repository with provided base repository."""
        cached_repo = RepositoryFactory.create_cached_repository(
            base_repository=mock_repository, cache_ttl=300
        )
        assert isinstance(cached_repo, CachedJokeRepository)
        assert cached_repo._repository is mock_repository

    def test_create_repository_http_with_enum(self):
        """Test creating repository using enum."""
        repo = RepositoryFactory.create_repository(RepositoryType.HTTP)
        assert isinstance(repo, HTTPJokeRepository)

    def test_create_repository_http_with_string(self):
        """Test creating repository using string."""
        repo = RepositoryFactory.create_repository("http")
        assert isinstance(repo, HTTPJokeRepository)

    def test_create_repository_cached_with_enum(self):
        """Test creating cached repository using enum."""
        repo = RepositoryFactory.create_repository(RepositoryType.CACHED)
        assert isinstance(repo, CachedJokeRepository)

    def test_create_repository_cached_with_string(self):
        """Test creating cached repository using string."""
        repo = RepositoryFactory.create_repository("cached")
        assert isinstance(repo, CachedJokeRepository)

    def test_create_repository_invalid_type(self):
        """Test that invalid repository type raises error."""
        with pytest.raises(ValueError) as exc_info:
            RepositoryFactory.create_repository("invalid_type")

        assert "invalid_type" in str(exc_info.value).lower()
        assert "valid types" in str(exc_info.value).lower()

    def test_create_repository_with_kwargs(self):
        """Test passing kwargs to factory method."""
        repo = RepositoryFactory.create_repository("cached", cache_ttl=900)
        assert isinstance(repo, CachedJokeRepository)
        assert repo._default_ttl == 900


class TestGetJokeRepository:
    """Tests for get_joke_repository singleton function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_repository()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_repository()

    def test_get_default_repository(self):
        """Test getting default repository."""
        repo = get_joke_repository()
        assert repo is not None
        # Default should be cached
        assert isinstance(repo, CachedJokeRepository)

    def test_singleton_returns_same_instance(self):
        """Test that multiple calls return same instance."""
        repo1 = get_joke_repository()
        repo2 = get_joke_repository()
        assert repo1 is repo2

    def test_force_recreate(self):
        """Test forcing recreation of repository."""
        repo1 = get_joke_repository()
        repo2 = get_joke_repository(force_recreate=True)
        assert repo1 is not repo2

    def test_force_recreate_with_different_type(self):
        """Test forcing recreation with different type."""
        repo1 = get_joke_repository(repository_type="cached")
        repo2 = get_joke_repository(force_recreate=True, repository_type="http")
        assert isinstance(repo1, CachedJokeRepository)
        assert isinstance(repo2, HTTPJokeRepository)
        assert repo1 is not repo2

    def test_get_repository_with_custom_type(self):
        """Test getting repository with custom type."""
        repo = get_joke_repository(repository_type="http")
        assert isinstance(repo, HTTPJokeRepository)

    def test_reset_repository(self):
        """Test resetting the singleton."""
        repo1 = get_joke_repository()
        reset_repository()
        repo2 = get_joke_repository()
        assert repo1 is not repo2


class TestRepositoryFactoryIntegration:
    """Integration tests for factory with actual repositories."""

    def test_http_repository_works(self):
        """Test that created HTTP repository is functional."""
        repo = RepositoryFactory.create_repository("http")
        assert repo.health_check() in [True, False]  # Depends on network

    def test_cached_repository_wraps_http(self):
        """Test that cached repository wraps HTTP repository."""
        cached = RepositoryFactory.create_repository("cached")
        assert isinstance(cached, CachedJokeRepository)
        assert isinstance(cached._repository, HTTPJokeRepository)
