"""
Unit tests for repositories/base.py

Tests for base repository interfaces and exceptions.
"""

import pytest

from repositories.base import (
    JokeNotFoundError,
    JokeRepository,
    JokeRepositoryError,
)


class TestJokeRepositoryError:
    """Tests for JokeRepositoryError exception."""

    def test_create_without_cause(self):
        """Test creating error without cause."""
        error = JokeRepositoryError("Test error")
        assert str(error) == "Test error"
        assert error.cause is None

    def test_create_with_cause(self):
        """Test creating error with cause."""
        cause = ValueError("Original error")
        error = JokeRepositoryError("Test error", cause=cause)
        assert str(error) == "Test error"
        assert error.cause is cause


class TestJokeNotFoundError:
    """Tests for JokeNotFoundError exception."""

    def test_create_error(self):
        """Test creating JokeNotFoundError."""
        error = JokeNotFoundError(42)
        assert error.joke_id == 42
        assert "42" in str(error)
        assert "not found" in str(error).lower()

    def test_is_subclass_of_repository_error(self):
        """Test that JokeNotFoundError is subclass of JokeRepositoryError."""
        error = JokeNotFoundError(1)
        assert isinstance(error, JokeRepositoryError)


class TestJokeRepositoryInterface:
    """Tests for JokeRepository abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that JokeRepository cannot be instantiated directly."""
        with pytest.raises(TypeError):
            JokeRepository()

    def test_mock_implementation_works(self, mock_repository):
        """Test that mock implementation satisfies the interface."""
        assert isinstance(mock_repository, JokeRepository)

        # Test all methods are implemented
        joke = mock_repository.get_random_joke()
        assert joke is not None

        jokes = mock_repository.get_random_jokes(10)
        assert jokes is not None

        joke_by_id = mock_repository.get_joke_by_id(1)
        assert joke_by_id is not None

        jokes_by_type = mock_repository.get_jokes_by_type("general")
        assert jokes_by_type is not None

        health = mock_repository.health_check()
        assert isinstance(health, bool)
