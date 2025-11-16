"""
Pytest configuration and shared fixtures.

This module provides common fixtures and configuration for all tests.
"""

from typing import Annotated

import pytest
from pydantic import Field

from repositories.base import JokeRepository
from utils.model import Joke, Jokes


# Sample test data
@pytest.fixture
def sample_joke() -> Joke:
    """Return a sample joke for testing."""
    return Joke(
        type="general",
        setup="Why did the chicken cross the road?",
        punchline="To get to the other side!",
        id=1,
    )


@pytest.fixture
def sample_jokes() -> Jokes:
    """Return a collection of sample jokes for testing."""
    return Jokes(
        jokes=[
            Joke(
                type="programming",
                setup="Why do programmers prefer dark mode?",
                punchline="Because light attracts bugs!",
                id=1,
            ),
            Joke(
                type="programming",
                setup="How many programmers does it take to change a light bulb?",
                punchline="None, that's a hardware problem!",
                id=2,
            ),
            Joke(
                type="general",
                setup="Why did the scarecrow win an award?",
                punchline="Because he was outstanding in his field!",
                id=3,
            ),
        ]
    )


class MockJokeRepository(JokeRepository):
    """Mock repository for testing."""

    def __init__(self):
        self.calls = {
            "get_random_joke": 0,
            "get_random_jokes": 0,
            "get_joke_by_id": 0,
            "get_jokes_by_type": 0,
            "health_check": 0,
        }
        self._jokes = {
            1: Joke(type="general", setup="Setup 1", punchline="Punchline 1", id=1),
            2: Joke(type="programming", setup="Setup 2", punchline="Punchline 2", id=2),
            3: Joke(type="general", setup="Setup 3", punchline="Punchline 3", id=3),
        }

    def get_random_joke(self) -> Joke:
        self.calls["get_random_joke"] += 1
        return self._jokes[1]

    def get_random_jokes(self, count: int = 10) -> Jokes:
        self.calls["get_random_jokes"] += 1
        return Jokes(jokes=list(self._jokes.values()))

    def get_joke_by_id(self, joke_id: Annotated[int, Field(ge=1, le=451)]) -> Joke:
        self.calls["get_joke_by_id"] += 1
        if joke_id not in self._jokes:
            from repositories.base import JokeNotFoundError

            raise JokeNotFoundError(joke_id)
        return self._jokes[joke_id]

    def get_jokes_by_type(self, joke_type: str) -> Jokes:
        self.calls["get_jokes_by_type"] += 1
        filtered = [j for j in self._jokes.values() if j.type == joke_type]
        return Jokes(jokes=filtered)

    def health_check(self) -> bool:
        self.calls["health_check"] += 1
        return True


@pytest.fixture
def mock_repository() -> MockJokeRepository:
    """Return a mock repository for testing."""
    return MockJokeRepository()


@pytest.fixture
def sample_joke_dict() -> dict:
    """Return a sample joke as dictionary (API response format)."""
    return {
        "type": "general",
        "setup": "Why did the chicken cross the road?",
        "punchline": "To get to the other side!",
        "id": 42,
    }


@pytest.fixture
def sample_jokes_list() -> list[dict]:
    """Return a list of sample jokes as dictionaries."""
    return [
        {
            "type": "programming",
            "setup": "Why do programmers prefer dark mode?",
            "punchline": "Because light attracts bugs!",
            "id": 1,
        },
        {
            "type": "programming",
            "setup": "How many programmers does it take to change a light bulb?",
            "punchline": "None, that's a hardware problem!",
            "id": 2,
        },
    ]
