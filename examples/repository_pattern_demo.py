#!/usr/bin/env python3
"""
Demo script showcasing the Repository Pattern implementation.

This script demonstrates how to use the different repository implementations
and their benefits in terms of abstraction, caching, and testability.
"""

from repositories import (
    get_joke_repository,
    HTTPJokeRepository,
    CachedJokeRepository,
    RepositoryFactory,
    RepositoryType,
)
from utils.logger import log


def demo_basic_usage():
    """Demonstrate basic repository usage."""
    log.info("=" * 70)
    log.info("1. BASIC REPOSITORY USAGE")
    log.info("=" * 70)

    # Get the default repository (cached)
    repo = get_joke_repository()
    log.info(f"Repository: {repo}\n")

    # Fetch a random joke
    log.info("Fetching a random joke...")
    joke = repo.get_random_joke()
    log.info(f"  Type: {joke.type}")
    log.info(f"  Setup: {joke.setup}")
    log.info(f"  Punchline: {joke.punchline}")
    log.info(f"  ID: {joke.id}\n")


def demo_http_repository():
    """Demonstrate direct HTTP repository usage."""
    log.info("=" * 70)
    log.info("2. HTTP REPOSITORY (No Cache)")
    log.info("=" * 70)

    # Create an HTTP repository directly
    http_repo = RepositoryFactory.create_http_repository()
    log.info(f"Repository: {http_repo}\n")

    # Fetch joke by ID
    log.info("Fetching joke by ID (42)...")
    joke = http_repo.get_joke_by_id(42)
    log.info(f"  {joke.setup}")
    log.info(f"  → {joke.punchline}\n")


def demo_cached_repository():
    """Demonstrate cached repository with statistics."""
    log.info("=" * 70)
    log.info("3. CACHED REPOSITORY DEMONSTRATION")
    log.info("=" * 70)

    # Create a cached repository
    cached_repo = RepositoryFactory.create_cached_repository(cache_ttl=600)
    log.info(f"Repository: {cached_repo}\n")

    # First fetch - cache miss
    log.info("First fetch of joke ID 100 (cache MISS expected)...")
    joke1 = cached_repo.get_joke_by_id(100)
    stats1 = cached_repo.get_cache_stats()
    log.info(f"  Joke: {joke1.setup}")
    log.info(f"  Cache stats: {stats1}\n")

    # Second fetch - cache hit
    log.info("Second fetch of joke ID 100 (cache HIT expected)...")
    joke2 = cached_repo.get_joke_by_id(100)
    stats2 = cached_repo.get_cache_stats()
    log.info(f"  Joke: {joke2.setup}")
    log.info(f"  Cache stats: {stats2}")
    log.info(f"  Same object? {joke1 is joke2}\n")

    # Fetch by type - cache miss
    log.info("Fetching programming jokes (cache MISS expected)...")
    jokes = cached_repo.get_jokes_by_type("programming")
    stats3 = cached_repo.get_cache_stats()
    log.info(f"  Retrieved {len(jokes.jokes)} jokes")
    log.info(f"  Cache stats: {stats3}\n")

    # Fetch by type again - cache hit
    log.info("Fetching programming jokes again (cache HIT expected)...")
    jokes2 = cached_repo.get_jokes_by_type("programming")
    stats4 = cached_repo.get_cache_stats()
    log.info(f"  Retrieved {len(jokes2.jokes)} jokes")
    log.info(f"  Cache stats: {stats4}")
    log.info(f"  Same object? {jokes is jokes2}\n")


def demo_factory_pattern():
    """Demonstrate factory pattern usage."""
    log.info("=" * 70)
    log.info("4. FACTORY PATTERN")
    log.info("=" * 70)

    # Create different types of repositories using factory
    log.info("Creating repositories using factory...\n")

    # HTTP repository
    http_repo = RepositoryFactory.create_repository(
        repository_type=RepositoryType.HTTP,
        timeout=5.0
    )
    log.info(f"HTTP Repository: {http_repo}")

    # Cached repository
    cached_repo = RepositoryFactory.create_repository(
        repository_type=RepositoryType.CACHED,
        cache_ttl=300
    )
    log.info(f"Cached Repository: {cached_repo}\n")

    # Using string type
    repo_from_string = RepositoryFactory.create_repository(
        repository_type="cached"
    )
    log.info(f"Repository from string: {repo_from_string}\n")


def demo_health_check():
    """Demonstrate repository health check."""
    log.info("=" * 70)
    log.info("5. HEALTH CHECK")
    log.info("=" * 70)

    repo = get_joke_repository()
    log.info(f"Repository: {type(repo).__name__}\n")

    log.info("Performing health check...")
    is_healthy = repo.health_check()
    log.info(f"  Health status: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}\n")


def demo_abstraction_benefit():
    """Demonstrate the abstraction benefit of Repository Pattern."""
    log.info("=" * 70)
    log.info("6. ABSTRACTION BENEFIT")
    log.info("=" * 70)

    log.info("Repository Pattern allows working with any implementation:")
    log.info("The same code works with HTTP or Cached repositories!\n")

    def fetch_and_display_joke(repository, joke_id: int):
        """Generic function that works with any repository."""
        joke = repository.get_joke_by_id(joke_id)
        log.info(f"  [{repository.__class__.__name__}] {joke.setup}")
        log.info(f"    → {joke.punchline}")

    # Same function, different repositories
    http_repo = RepositoryFactory.create_repository("http")
    cached_repo = RepositoryFactory.create_repository("cached")

    joke_id = 25
    log.info(f"Fetching joke ID {joke_id} with different repositories:\n")

    fetch_and_display_joke(http_repo, joke_id)
    log.info("")
    fetch_and_display_joke(cached_repo, joke_id)
    log.info("")


def main():
    """Run all demonstrations."""
    log.info("\n")
    log.info("╔" + "═" * 68 + "╗")
    log.info("║" + " " * 15 + "REPOSITORY PATTERN DEMONSTRATION" + " " * 21 + "║")
    log.info("╚" + "═" * 68 + "╝")
    log.info("")

    try:
        demo_basic_usage()
        demo_http_repository()
        demo_cached_repository()
        demo_factory_pattern()
        demo_health_check()
        demo_abstraction_benefit()

        log.info("=" * 70)
        log.info("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY ✓")
        log.info("=" * 70)
        log.info("")

    except Exception as e:
        log.exception(f"\n❌ Error during demonstration: {e}")


if __name__ == "__main__":
    main()
