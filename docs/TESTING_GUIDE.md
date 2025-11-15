# Testing Guide

## Overview

This project has a comprehensive test suite covering unit tests and integration tests for all major components.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── test_repositories_base.py      # Tests for base repository interfaces
├── test_cached_repository.py      # Tests for cached repository decorator
├── test_factory.py                # Tests for repository factory
├── test_exceptions.py             # Tests for custom exceptions
├── test_config.py                 # Tests for configuration system
└── test_integration.py            # Integration tests
```

## Running Tests

### All Tests
```bash
uv run pytest tests/ -v
```

### Unit Tests Only
```bash
uv run pytest tests/ -v -m "not integration"
```

### Integration Tests Only
```bash
uv run pytest tests/ -v -m "integration"
```

### Specific Test File
```bash
uv run pytest tests/test_cached_repository.py -v
```

### Specific Test Class
```bash
uv run pytest tests/test_factory.py::TestRepositoryFactory -v
```

### Specific Test Method
```bash
uv run pytest tests/test_cached_repository.py::TestCachedJokeRepository::test_cache_hit_on_second_call -v
```

### With Coverage
```bash
uv run pytest tests/ --cov=repositories --cov=utils --cov-report=html
```

## Test Categories

### Unit Tests (83 tests)

**Repository Base Tests** (`test_repositories_base.py`)
- Exception creation and hierarchy
- Abstract interface validation
- Mock implementation testing

**Cached Repository Tests** (`test_cached_repository.py`)
- Cache entry creation and expiration
- Cache hit/miss statistics
- Cache clearing
- TTL configuration
- Different caching strategies for different methods

**Factory Tests** (`test_factory.py`)
- Repository factory methods
- Singleton pattern
- Different repository types
- Configuration options

**Exception Tests** (`test_exceptions.py`)
- Custom exception creation
- Exception hierarchy
- Exception catching

**Configuration Tests** (`test_config.py`)
- Settings loading
- Singleton pattern
- Validation
- Class attribute access

### Integration Tests (17 tests)

**HTTP Repository Integration** (`test_integration.py`)
- Real API calls
- Error handling
- Health checks

**Cached Repository Integration**
- Cache behavior with real API
- Performance improvements

**Factory Integration**
- Creating working repositories
- Singleton behavior

**End-to-End Tests**
- Complete joke retrieval flow
- Error handling flow
- Cache performance

## Test Coverage

Current coverage:
- **Unit tests**: 83 tests
- **Integration tests**: 17 tests
- **Total**: 100 tests
- **Success rate**: 100%

## Writing New Tests

### Unit Test Example
```python
import pytest
from repositories import CachedJokeRepository

def test_cache_stores_jokes(mock_repository):
    """Test that cache stores jokes correctly."""
    cached_repo = CachedJokeRepository(mock_repository)

    joke1 = cached_repo.get_joke_by_id(1)
    joke2 = cached_repo.get_joke_by_id(1)

    assert joke1 is joke2  # Same object from cache
    assert mock_repository.calls['get_joke_by_id'] == 1
```

### Integration Test Example
```python
import pytest
from repositories import get_joke_repository

@pytest.mark.integration
def test_repository_fetches_real_joke():
    """Test fetching real joke from API."""
    try:
        repo = get_joke_repository()
        joke = repo.get_random_joke()
        assert joke.id > 0
        assert len(joke.setup) > 0
    except JokeRepositoryError:
        pytest.skip("API is not accessible")
```

## Fixtures

### Available Fixtures (from `conftest.py`)

- **`sample_joke`** - A Joke instance for testing
- **`sample_jokes`** - A Jokes collection for testing
- **`mock_repository`** - MockJokeRepository instance
- **`sample_joke_dict`** - Joke as dictionary (API format)
- **`sample_jokes_list`** - List of jokes as dictionaries

### Using Fixtures
```python
def test_something(sample_joke, mock_repository):
    """Test using fixtures."""
    # sample_joke and mock_repository are automatically injected
    assert sample_joke.id == 1
    assert isinstance(mock_repository, JokeRepository)
```

## Test Markers

### Available Markers
- `@pytest.mark.integration` - Integration tests (may require network)
- `@pytest.mark.slow` - Slow tests

### Using Markers
```python
@pytest.mark.integration
def test_real_api_call():
    """This test makes real API calls."""
    pass
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: uv sync --extra dev
      - name: Run tests
        run: uv run pytest tests/ -v --cov=repositories --cov=utils
```

## Troubleshooting

### Issue: Tests fail with import errors
**Solution**: Install dev dependencies
```bash
uv sync --extra dev
```

### Issue: Integration tests fail
**Solution**: Integration tests require network access. Skip them or check your connection.
```bash
uv run pytest tests/ -v -m "not integration"
```

### Issue: Slow test runs
**Solution**: Run unit tests only (much faster)
```bash
uv run pytest tests/ -v -m "not integration"
```

## Best Practices

1. **Write tests first** - TDD approach
2. **Use fixtures** - Don't repeat setup code
3. **Mock external dependencies** - For unit tests
4. **Mark integration tests** - Use `@pytest.mark.integration`
5. **Test edge cases** - Not just happy path
6. **Keep tests fast** - Unit tests should be < 1s
7. **Clear test names** - Describe what is being tested
8. **One assertion per test** - When possible

## Test Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 100 |
| Unit Tests | 83 |
| Integration Tests | 17 |
| Success Rate | 100% |
| Avg Test Time | ~0.03s |
| Total Test Time | ~2.5s (unit only) |

## Future Improvements

- [ ] Add performance benchmarks
- [ ] Add property-based tests (Hypothesis)
- [ ] Add mutation testing
- [ ] Increase coverage to 100%
- [ ] Add stress tests
- [ ] Add security tests

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
