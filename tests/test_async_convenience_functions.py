"""
Tests for async convenience functions.

Tests the singleton-based async convenience functions:
- aget_joke()
- aget_ten_jokes()
- aget_joke_by_id()
- aget_jokes_by_type()
"""

from unittest.mock import AsyncMock, patch

import pytest

from utils.exceptions import (
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
    JokeAPITimeoutError,
)
from utils.model import Joke, Jokes
from utils.RequestAPIJokes import (
    _aclient,
    aget_joke,
    aget_joke_by_id,
    aget_jokes_by_type,
    aget_ten_jokes,
)


@pytest.fixture
def sample_joke():
    """Fixture providing a sample Joke instance."""
    return Joke(
        id=42,
        type="general",
        setup="Why don't scientists trust atoms?",
        punchline="Because they make up everything!",
    )


@pytest.fixture
def sample_jokes():
    """Fixture providing a sample Jokes instance."""
    jokes = [
        Joke(id=i, type="general", setup=f"Setup {i}", punchline=f"Punchline {i}")
        for i in range(1, 11)
    ]
    return Jokes(jokes=jokes)


class TestAgetJoke:
    """Tests for aget_joke() convenience function."""

    @pytest.mark.asyncio
    async def test_aget_joke_success(self, sample_joke):
        """Test successful joke retrieval via aget_joke()."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.return_value = sample_joke

            result = await aget_joke()

            assert result == sample_joke
            assert result.id == 42
            assert result.setup == "Why don't scientists trust atoms?"
            mock_get_joke.assert_called_once()

    @pytest.mark.asyncio
    async def test_aget_joke_timeout_error(self):
        """Test that timeout errors are propagated from singleton client."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await aget_joke()

    @pytest.mark.asyncio
    async def test_aget_joke_connection_error(self):
        """Test that connection errors are propagated."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await aget_joke()

    @pytest.mark.asyncio
    async def test_aget_joke_http_error(self):
        """Test that HTTP errors are propagated."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.side_effect = JokeAPIHTTPError(
                message="Server error", status_code=500, response_text="Internal Server Error"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await aget_joke()

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_aget_joke_parse_error(self):
        """Test that parsing errors are propagated."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.side_effect = JokeAPIParseError("Invalid JSON")

            with pytest.raises(JokeAPIParseError):
                await aget_joke()

    @pytest.mark.asyncio
    async def test_aget_joke_multiple_calls(self, sample_joke):
        """Test multiple consecutive calls to aget_joke()."""
        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            # Create different jokes for each call
            joke1 = Joke(id=1, type="general", setup="Setup 1", punchline="Punchline 1")
            joke2 = Joke(id=2, type="general", setup="Setup 2", punchline="Punchline 2")
            joke3 = Joke(id=3, type="general", setup="Setup 3", punchline="Punchline 3")

            mock_get_joke.side_effect = [joke1, joke2, joke3]

            result1 = await aget_joke()
            result2 = await aget_joke()
            result3 = await aget_joke()

            assert result1.id == 1
            assert result2.id == 2
            assert result3.id == 3
            assert mock_get_joke.call_count == 3


class TestAgetTenJokes:
    """Tests for aget_ten_jokes() convenience function."""

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_success(self, sample_jokes):
        """Test successful retrieval of ten jokes."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.return_value = sample_jokes

            result = await aget_ten_jokes()

            assert result == sample_jokes
            assert len(result.jokes) == 10
            assert all(isinstance(joke, Joke) for joke in result.jokes)
            mock_get_ten.assert_called_once()

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_timeout_error(self):
        """Test timeout error propagation."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await aget_ten_jokes()

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_connection_error(self):
        """Test connection error propagation."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await aget_ten_jokes()

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_http_error(self):
        """Test HTTP error propagation."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.side_effect = JokeAPIHTTPError(
                message="Not found", status_code=404, response_text="Resource not found"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await aget_ten_jokes()

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_parse_error(self):
        """Test parse error propagation."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.side_effect = JokeAPIParseError("Malformed JSON")

            with pytest.raises(JokeAPIParseError):
                await aget_ten_jokes()

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_correct_count(self, sample_jokes):
        """Test that exactly 10 jokes are returned."""
        with patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten:
            mock_get_ten.return_value = sample_jokes

            result = await aget_ten_jokes()

            assert len(result.jokes) == 10


class TestAgetJokeById:
    """Tests for aget_joke_by_id() convenience function."""

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_success(self, sample_joke):
        """Test successful joke retrieval by ID."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.return_value = sample_joke

            result = await aget_joke_by_id(42)

            assert result == sample_joke
            assert result.id == 42
            mock_get_by_id.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_various_ids(self):
        """Test retrieval with different IDs."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            for joke_id in [1, 100, 200, 451]:
                joke = Joke(id=joke_id, type="general", setup="Setup", punchline="Punchline")
                mock_get_by_id.return_value = joke

                result = await aget_joke_by_id(joke_id)

                assert result.id == joke_id
                mock_get_by_id.assert_called_with(joke_id)

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_timeout_error(self):
        """Test timeout error propagation."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await aget_joke_by_id(1)

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_connection_error(self):
        """Test connection error propagation."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await aget_joke_by_id(1)

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_not_found(self):
        """Test 404 error when joke doesn't exist."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.side_effect = JokeAPIHTTPError(
                message="Joke not found", status_code=404, response_text="Not Found"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await aget_joke_by_id(999)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_parse_error(self):
        """Test parse error propagation."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            mock_get_by_id.side_effect = JokeAPIParseError("Invalid data")

            with pytest.raises(JokeAPIParseError):
                await aget_joke_by_id(1)

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_boundary_values(self):
        """Test boundary ID values (1 and 451)."""
        with patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id:
            # Test ID 1
            joke1 = Joke(id=1, type="general", setup="First", punchline="Joke")
            mock_get_by_id.return_value = joke1
            result1 = await aget_joke_by_id(1)
            assert result1.id == 1

            # Test ID 451
            joke451 = Joke(id=451, type="general", setup="Last", punchline="Joke")
            mock_get_by_id.return_value = joke451
            result451 = await aget_joke_by_id(451)
            assert result451.id == 451


class TestAgetJokesByType:
    """Tests for aget_jokes_by_type() convenience function."""

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_general(self, sample_jokes):
        """Test getting jokes of type 'general'."""
        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.return_value = sample_jokes

            result = await aget_jokes_by_type("general")

            assert result == sample_jokes
            mock_get_by_type.assert_called_once_with("general")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_programming(self):
        """Test getting jokes of type 'programming'."""
        programming_jokes = Jokes(
            jokes=[
                Joke(id=i, type="programming", setup=f"Code {i}", punchline=f"Bug {i}")
                for i in range(1, 6)
            ]
        )

        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.return_value = programming_jokes

            result = await aget_jokes_by_type("programming")

            assert len(result.jokes) == 5
            assert all(joke.type == "programming" for joke in result.jokes)
            mock_get_by_type.assert_called_once_with("programming")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_knock_knock(self):
        """Test getting jokes of type 'knock-knock'."""
        knock_knock_jokes = Jokes(
            jokes=[
                Joke(id=i, type="knock-knock", setup="Knock knock", punchline=f"Who's there? {i}")
                for i in range(1, 4)
            ]
        )

        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.return_value = knock_knock_jokes

            result = await aget_jokes_by_type("knock-knock")

            assert len(result.jokes) == 3
            assert all(joke.type == "knock-knock" for joke in result.jokes)
            mock_get_by_type.assert_called_once_with("knock-knock")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_timeout_error(self):
        """Test timeout error propagation."""
        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await aget_jokes_by_type("general")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_connection_error(self):
        """Test connection error propagation."""
        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await aget_jokes_by_type("programming")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_http_error(self):
        """Test HTTP error propagation."""
        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.side_effect = JokeAPIHTTPError(
                message="Invalid type", status_code=400, response_text="Bad Request"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await aget_jokes_by_type("invalid_type")

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_parse_error(self):
        """Test parse error propagation."""
        with patch.object(
            _aclient, "get_jokes_by_type", new_callable=AsyncMock
        ) as mock_get_by_type:
            mock_get_by_type.side_effect = JokeAPIParseError("Invalid response format")

            with pytest.raises(JokeAPIParseError):
                await aget_jokes_by_type("general")

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_all_types(self):
        """Test all valid joke types."""
        valid_types = ["general", "programming", "knock-knock", "dad"]

        for joke_type in valid_types:
            jokes = Jokes(jokes=[Joke(id=1, type=joke_type, setup="Setup", punchline="Punchline")])

            with patch.object(
                _aclient, "get_jokes_by_type", new_callable=AsyncMock
            ) as mock_get_by_type:
                mock_get_by_type.return_value = jokes

                result = await aget_jokes_by_type(joke_type)

                assert result.jokes[0].type == joke_type
                mock_get_by_type.assert_called_once_with(joke_type)


class TestAsyncConvenienceFunctionsSingletonBehavior:
    """Tests for singleton behavior of async convenience functions."""

    @pytest.mark.asyncio
    async def test_singleton_client_reuse(self, sample_joke):
        """Test that all convenience functions use the same singleton client."""
        # This test verifies that _aclient is reused
        from utils.RequestAPIJokes import _aclient as client1
        from utils.RequestAPIJokes import _aclient as client2

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_concurrent_calls_to_same_function(self, sample_joke):
        """Test concurrent calls to the same convenience function."""
        import asyncio

        jokes = [
            Joke(id=i, type="general", setup=f"Setup {i}", punchline=f"Punchline {i}")
            for i in range(1, 6)
        ]

        with patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke:
            mock_get_joke.side_effect = jokes

            # Make 5 concurrent calls
            results = await asyncio.gather(*[aget_joke() for _ in range(5)])

            assert len(results) == 5
            assert mock_get_joke.call_count == 5

    @pytest.mark.asyncio
    async def test_concurrent_calls_to_different_functions(self, sample_joke, sample_jokes):
        """Test concurrent calls to different convenience functions."""
        import asyncio

        with (
            patch.object(_aclient, "get_joke", new_callable=AsyncMock) as mock_get_joke,
            patch.object(_aclient, "get_ten_jokes", new_callable=AsyncMock) as mock_get_ten,
            patch.object(_aclient, "get_joke_by_id", new_callable=AsyncMock) as mock_get_by_id,
        ):
            mock_get_joke.return_value = sample_joke
            mock_get_ten.return_value = sample_jokes
            mock_get_by_id.return_value = sample_joke

            # Make concurrent calls to different functions
            results = await asyncio.gather(
                aget_joke(),
                aget_ten_jokes(),
                aget_joke_by_id(42),
            )

            assert len(results) == 3
            assert isinstance(results[0], Joke)
            assert isinstance(results[1], Jokes)
            assert isinstance(results[2], Joke)
