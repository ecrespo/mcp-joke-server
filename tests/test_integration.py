"""
Integration tests for the joke service.

These tests verify that different components work together correctly.
Note: Some tests may make real HTTP calls and can fail if the API is down.
"""

import pytest
from repositories import (
    get_joke_repository,
    HTTPJokeRepository,
    CachedJokeRepository,
    RepositoryFactory,
    reset_repository,
)
from repositories.base import JokeNotFoundError, JokeRepositoryError
from utils.model import Joke, Jokes


@pytest.mark.integration
class TestHTTPRepositoryIntegration:
    """Integration tests for HTTP repository with real API."""

    @pytest.fixture
    def http_repo(self):
        """Create an HTTP repository for testing."""
        return RepositoryFactory.create_http_repository(timeout=10.0)

    def test_get_random_joke(self, http_repo):
        """Test fetching a random joke from real API."""
        try:
            joke = http_repo.get_random_joke()
            assert isinstance(joke, Joke)
            assert joke.id > 0
            assert len(joke.setup) > 0
            assert len(joke.punchline) > 0
            assert joke.type in ["general", "knock-knock", "programming", "dad"]
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_get_joke_by_id(self, http_repo):
        """Test fetching a specific joke by ID."""
        try:
            joke = http_repo.get_joke_by_id(1)
            assert isinstance(joke, Joke)
            assert joke.id == 1
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_get_joke_by_invalid_id(self, http_repo):
        """Test that invalid ID raises JokeNotFoundError."""
        try:
            with pytest.raises(JokeNotFoundError):
                http_repo.get_joke_by_id(999999)
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_get_jokes_by_type(self, http_repo):
        """Test fetching jokes by type."""
        try:
            jokes = http_repo.get_jokes_by_type("programming")
            assert isinstance(jokes, Jokes)
            assert len(jokes.jokes) > 0
            # Verify all jokes are of requested type
            for joke in jokes.jokes:
                assert joke.type == "programming"
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_health_check(self, http_repo):
        """Test health check with real API."""
        result = http_repo.health_check()
        # Result should be True if API is up, False otherwise
        assert isinstance(result, bool)


@pytest.mark.integration
class TestCachedRepositoryIntegration:
    """Integration tests for cached repository."""

    @pytest.fixture
    def cached_repo(self):
        """Create a cached repository wrapping HTTP repository."""
        http_repo = RepositoryFactory.create_http_repository(timeout=10.0)
        return CachedJokeRepository(http_repo, default_ttl=60)

    def test_cache_hit_on_second_call(self, cached_repo):
        """Test that second call hits the cache."""
        try:
            # First call - should miss cache
            joke1 = cached_repo.get_joke_by_id(1)
            stats_after_first = cached_repo.get_cache_stats()
            assert stats_after_first['misses'] == 1
            assert stats_after_first['hits'] == 0

            # Second call - should hit cache
            joke2 = cached_repo.get_joke_by_id(1)
            stats_after_second = cached_repo.get_cache_stats()
            assert stats_after_second['misses'] == 1
            assert stats_after_second['hits'] == 1

            # Should be same object
            assert joke1 is joke2
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_cache_different_jokes(self, cached_repo):
        """Test caching multiple different jokes."""
        try:
            joke1 = cached_repo.get_joke_by_id(1)
            joke2 = cached_repo.get_joke_by_id(2)
            joke3 = cached_repo.get_joke_by_id(3)

            stats = cached_repo.get_cache_stats()
            assert stats['cache_size'] == 3
            assert stats['misses'] == 3

            # Access cached jokes
            joke1_cached = cached_repo.get_joke_by_id(1)
            assert joke1 is joke1_cached
            stats = cached_repo.get_cache_stats()
            assert stats['hits'] == 1
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_random_jokes_not_cached(self, cached_repo):
        """Test that random jokes are not cached."""
        try:
            joke1 = cached_repo.get_random_joke()
            joke2 = cached_repo.get_random_joke()

            # Cache should be empty for random jokes
            stats = cached_repo.get_cache_stats()
            assert stats['cache_size'] == 0
        except JokeRepositoryError:
            pytest.skip("API is not accessible")


@pytest.mark.integration
class TestFactoryIntegration:
    """Integration tests for repository factory."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_repository()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_repository()

    def test_factory_creates_working_http_repo(self):
        """Test that factory creates a working HTTP repository."""
        repo = RepositoryFactory.create_repository("http")
        assert isinstance(repo, HTTPJokeRepository)
        # Test it works
        result = repo.health_check()
        assert isinstance(result, bool)

    def test_factory_creates_working_cached_repo(self):
        """Test that factory creates a working cached repository."""
        repo = RepositoryFactory.create_repository("cached")
        assert isinstance(repo, CachedJokeRepository)
        assert isinstance(repo._repository, HTTPJokeRepository)

    def test_get_joke_repository_default(self):
        """Test default repository from get_joke_repository."""
        repo = get_joke_repository()
        assert isinstance(repo, CachedJokeRepository)

        # Should work
        result = repo.health_check()
        assert isinstance(result, bool)

    def test_get_joke_repository_singleton(self):
        """Test singleton behavior of get_joke_repository."""
        repo1 = get_joke_repository()
        repo2 = get_joke_repository()
        assert repo1 is repo2


@pytest.mark.integration
class TestEndToEndJokeFlow:
    """End-to-end integration tests simulating real usage."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_repository()

    def teardown_method(self):
        """Reset singleton after each test."""
        reset_repository()

    def test_complete_joke_retrieval_flow(self):
        """Test complete flow of retrieving jokes."""
        try:
            # Get repository
            repo = get_joke_repository()

            # Get random joke
            random_joke = repo.get_random_joke()
            assert isinstance(random_joke, Joke)

            # Get specific joke
            specific_joke = repo.get_joke_by_id(1)
            assert isinstance(specific_joke, Joke)
            assert specific_joke.id == 1

            # Get jokes by type
            programming_jokes = repo.get_jokes_by_type("programming")
            assert isinstance(programming_jokes, Jokes)
            assert len(programming_jokes.jokes) > 0

            # Verify cache is working
            if isinstance(repo, CachedJokeRepository):
                stats = repo.get_cache_stats()
                assert stats['cache_size'] > 0  # Should have cached something

        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_error_handling_flow(self):
        """Test error handling in complete flow."""
        try:
            repo = get_joke_repository()

            # Try to get non-existent joke
            with pytest.raises(JokeNotFoundError) as exc_info:
                repo.get_joke_by_id(999999)

            assert exc_info.value.joke_id == 999999

        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_cache_performance(self):
        """Test that cache improves performance."""
        try:
            repo = get_joke_repository()
            assert isinstance(repo, CachedJokeRepository)

            # First fetch - cache miss
            joke1 = repo.get_joke_by_id(1)
            stats1 = repo.get_cache_stats()

            # Multiple fetches of same joke - should be fast (cached)
            for _ in range(10):
                joke = repo.get_joke_by_id(1)
                assert joke is joke1  # Same object

            stats2 = repo.get_cache_stats()
            # Should have many cache hits
            assert stats2['hits'] == 10
            assert stats2['misses'] == 1
            assert stats2['hit_rate_percent'] > 90

        except JokeRepositoryError:
            pytest.skip("API is not accessible")


@pytest.mark.integration
class TestRepositorySwapping:
    """Test swapping between different repository implementations."""

    def test_swap_http_to_cached(self):
        """Test swapping from HTTP to cached repository."""
        # Start with HTTP
        http_repo = RepositoryFactory.create_repository("http")
        assert isinstance(http_repo, HTTPJokeRepository)

        # Swap to cached
        cached_repo = CachedJokeRepository(http_repo)
        assert isinstance(cached_repo, CachedJokeRepository)

        # Should work the same
        try:
            joke1 = http_repo.get_joke_by_id(1)
            joke2 = cached_repo.get_joke_by_id(1)
            assert joke1.id == joke2.id
        except JokeRepositoryError:
            pytest.skip("API is not accessible")

    def test_mock_to_cached(self, mock_repository):
        """Test using cached repository with mock."""
        cached_repo = CachedJokeRepository(mock_repository)

        # Should work with mock
        joke1 = cached_repo.get_joke_by_id(1)
        joke2 = cached_repo.get_joke_by_id(1)  # Cache hit

        assert joke1 is joke2
        assert mock_repository.calls['get_joke_by_id'] == 1

        stats = cached_repo.get_cache_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
