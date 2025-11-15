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


def demo_basic_usage():
    """Demonstrate basic repository usage."""
    print("=" * 70)
    print("1. BASIC REPOSITORY USAGE")
    print("=" * 70)

    # Get the default repository (cached)
    repo = get_joke_repository()
    print(f"Repository: {repo}\n")

    # Fetch a random joke
    print("Fetching a random joke...")
    joke = repo.get_random_joke()
    print(f"  Type: {joke.type}")
    print(f"  Setup: {joke.setup}")
    print(f"  Punchline: {joke.punchline}")
    print(f"  ID: {joke.id}\n")


def demo_http_repository():
    """Demonstrate direct HTTP repository usage."""
    print("=" * 70)
    print("2. HTTP REPOSITORY (No Cache)")
    print("=" * 70)

    # Create an HTTP repository directly
    http_repo = RepositoryFactory.create_http_repository()
    print(f"Repository: {http_repo}\n")

    # Fetch joke by ID
    print("Fetching joke by ID (42)...")
    joke = http_repo.get_joke_by_id(42)
    print(f"  {joke.setup}")
    print(f"  → {joke.punchline}\n")


def demo_cached_repository():
    """Demonstrate cached repository with statistics."""
    print("=" * 70)
    print("3. CACHED REPOSITORY DEMONSTRATION")
    print("=" * 70)

    # Create a cached repository
    cached_repo = RepositoryFactory.create_cached_repository(cache_ttl=600)
    print(f"Repository: {cached_repo}\n")

    # First fetch - cache miss
    print("First fetch of joke ID 100 (cache MISS expected)...")
    joke1 = cached_repo.get_joke_by_id(100)
    stats1 = cached_repo.get_cache_stats()
    print(f"  Joke: {joke1.setup}")
    print(f"  Cache stats: {stats1}\n")

    # Second fetch - cache hit
    print("Second fetch of joke ID 100 (cache HIT expected)...")
    joke2 = cached_repo.get_joke_by_id(100)
    stats2 = cached_repo.get_cache_stats()
    print(f"  Joke: {joke2.setup}")
    print(f"  Cache stats: {stats2}")
    print(f"  Same object? {joke1 is joke2}\n")

    # Fetch by type - cache miss
    print("Fetching programming jokes (cache MISS expected)...")
    jokes = cached_repo.get_jokes_by_type("programming")
    stats3 = cached_repo.get_cache_stats()
    print(f"  Retrieved {len(jokes.jokes)} jokes")
    print(f"  Cache stats: {stats3}\n")

    # Fetch by type again - cache hit
    print("Fetching programming jokes again (cache HIT expected)...")
    jokes2 = cached_repo.get_jokes_by_type("programming")
    stats4 = cached_repo.get_cache_stats()
    print(f"  Retrieved {len(jokes2.jokes)} jokes")
    print(f"  Cache stats: {stats4}")
    print(f"  Same object? {jokes is jokes2}\n")


def demo_factory_pattern():
    """Demonstrate factory pattern usage."""
    print("=" * 70)
    print("4. FACTORY PATTERN")
    print("=" * 70)

    # Create different types of repositories using factory
    print("Creating repositories using factory...\n")

    # HTTP repository
    http_repo = RepositoryFactory.create_repository(
        repository_type=RepositoryType.HTTP,
        timeout=5.0
    )
    print(f"HTTP Repository: {http_repo}")

    # Cached repository
    cached_repo = RepositoryFactory.create_repository(
        repository_type=RepositoryType.CACHED,
        cache_ttl=300
    )
    print(f"Cached Repository: {cached_repo}\n")

    # Using string type
    repo_from_string = RepositoryFactory.create_repository(
        repository_type="cached"
    )
    print(f"Repository from string: {repo_from_string}\n")


def demo_health_check():
    """Demonstrate repository health check."""
    print("=" * 70)
    print("5. HEALTH CHECK")
    print("=" * 70)

    repo = get_joke_repository()
    print(f"Repository: {type(repo).__name__}\n")

    print("Performing health check...")
    is_healthy = repo.health_check()
    print(f"  Health status: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}\n")


def demo_abstraction_benefit():
    """Demonstrate the abstraction benefit of Repository Pattern."""
    print("=" * 70)
    print("6. ABSTRACTION BENEFIT")
    print("=" * 70)

    print("Repository Pattern allows working with any implementation:")
    print("The same code works with HTTP or Cached repositories!\n")

    def fetch_and_display_joke(repository, joke_id: int):
        """Generic function that works with any repository."""
        joke = repository.get_joke_by_id(joke_id)
        print(f"  [{repository.__class__.__name__}] {joke.setup}")
        print(f"    → {joke.punchline}")

    # Same function, different repositories
    http_repo = RepositoryFactory.create_repository("http")
    cached_repo = RepositoryFactory.create_repository("cached")

    joke_id = 25
    print(f"Fetching joke ID {joke_id} with different repositories:\n")

    fetch_and_display_joke(http_repo, joke_id)
    print()
    fetch_and_display_joke(cached_repo, joke_id)
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "REPOSITORY PATTERN DEMONSTRATION" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    try:
        demo_basic_usage()
        demo_http_repository()
        demo_cached_repository()
        demo_factory_pattern()
        demo_health_check()
        demo_abstraction_benefit()

        print("=" * 70)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY ✓")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
