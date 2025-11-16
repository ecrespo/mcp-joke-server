"""
Tests for async MCP tools.

Tests the async tool variants that are exposed via FastMCP:
- tool_aget_joke()
- tool_aget_joke_by_id()
- tool_aget_joke_by_type()
"""

import pytest
from unittest.mock import AsyncMock, patch

from main import tool_aget_joke, tool_aget_joke_by_id, tool_aget_joke_by_type
from utils.model import Joke, Jokes
from utils.exceptions import (
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
)


# Access the underlying functions from the decorated tools
# FastMCP wraps functions in FunctionTool objects
_tool_aget_joke_func = tool_aget_joke.fn if hasattr(tool_aget_joke, 'fn') else tool_aget_joke
_tool_aget_joke_by_id_func = tool_aget_joke_by_id.fn if hasattr(tool_aget_joke_by_id, 'fn') else tool_aget_joke_by_id
_tool_aget_joke_by_type_func = tool_aget_joke_by_type.fn if hasattr(tool_aget_joke_by_type, 'fn') else tool_aget_joke_by_type


@pytest.fixture
def sample_joke():
    """Fixture providing a sample Joke instance."""
    return Joke(
        id=42,
        type="general",
        setup="Why did the programmer quit his job?",
        punchline="Because he didn't get arrays!"
    )


@pytest.fixture
def sample_jokes():
    """Fixture providing a sample Jokes collection."""
    jokes = [
        Joke(id=i, type="programming", setup=f"Setup {i}", punchline=f"Punchline {i}")
        for i in range(1, 6)
    ]
    return Jokes(jokes=jokes)


class TestToolAgetJoke:
    """Tests for tool_aget_joke() async MCP tool."""

    @pytest.mark.asyncio
    async def test_tool_aget_joke_success(self, sample_joke):
        """Test successful async joke retrieval via tool."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.return_value = sample_joke

            result = await _tool_aget_joke_func()

            assert isinstance(result, str)
            assert "Why did the programmer quit his job?" in result
            assert "Because he didn't get arrays!" in result
            mock_aget.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_aget_joke_format(self, sample_joke):
        """Test that the tool returns properly formatted joke string."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.return_value = sample_joke

            result = await _tool_aget_joke_func()

            # Should be in "setup\npunchline" format
            lines = result.split('\n')
            assert len(lines) >= 2
            assert sample_joke.setup in result
            assert sample_joke.punchline in result

    @pytest.mark.asyncio
    async def test_tool_aget_joke_timeout_error(self):
        """Test timeout error propagation in tool."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await _tool_aget_joke_func()

    @pytest.mark.asyncio
    async def test_tool_aget_joke_connection_error(self):
        """Test connection error propagation in tool."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await _tool_aget_joke_func()

    @pytest.mark.asyncio
    async def test_tool_aget_joke_http_error(self):
        """Test HTTP error propagation in tool."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = JokeAPIHTTPError(
                message="Server error",
                status_code=503,
                response_text="Service Unavailable"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await _tool_aget_joke_func()

            assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_tool_aget_joke_parse_error(self):
        """Test parse error propagation in tool."""
        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = JokeAPIParseError("Invalid JSON")

            with pytest.raises(JokeAPIParseError):
                await _tool_aget_joke_func()

    @pytest.mark.asyncio
    async def test_tool_aget_joke_multiple_calls(self):
        """Test multiple consecutive calls return different jokes."""
        jokes = [
            Joke(id=1, type="general", setup="Setup 1", punchline="Punchline 1"),
            Joke(id=2, type="general", setup="Setup 2", punchline="Punchline 2"),
            Joke(id=3, type="general", setup="Setup 3", punchline="Punchline 3"),
        ]

        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = jokes

            result1 = await _tool_aget_joke_func()
            result2 = await _tool_aget_joke_func()
            result3 = await _tool_aget_joke_func()

            assert "Setup 1" in result1
            assert "Setup 2" in result2
            assert "Setup 3" in result3
            assert mock_aget.call_count == 3


class TestToolAgetJokeById:
    """Tests for tool_aget_joke_by_id() async MCP tool."""

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_success(self, sample_joke):
        """Test successful joke retrieval by ID via tool."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.return_value = sample_joke

            result = await _tool_aget_joke_by_id_func(42)

            assert isinstance(result, str)
            assert sample_joke.setup in result
            assert sample_joke.punchline in result
            mock_aget_by_id.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_various_ids(self):
        """Test tool with different joke IDs."""
        for joke_id in [1, 100, 200, 451]:
            joke = Joke(
                id=joke_id,
                type="general",
                setup=f"Setup for joke {joke_id}",
                punchline=f"Punchline for joke {joke_id}"
            )

            with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
                mock_aget_by_id.return_value = joke

                result = await _tool_aget_joke_by_id_func(joke_id)

                assert f"Setup for joke {joke_id}" in result
                assert f"Punchline for joke {joke_id}" in result
                mock_aget_by_id.assert_called_once_with(joke_id)

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_format(self, sample_joke):
        """Test that the tool returns properly formatted joke string."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.return_value = sample_joke

            result = await _tool_aget_joke_by_id_func(42)

            # Should contain both setup and punchline
            lines = result.split('\n')
            assert len(lines) >= 2
            assert sample_joke.setup in result
            assert sample_joke.punchline in result

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_timeout_error(self):
        """Test timeout error propagation."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await _tool_aget_joke_by_id_func(1)

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_connection_error(self):
        """Test connection error propagation."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await _tool_aget_joke_by_id_func(1)

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_not_found(self):
        """Test 404 error when joke doesn't exist."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.side_effect = JokeAPIHTTPError(
                message="Joke not found",
                status_code=404,
                response_text="Not Found"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await _tool_aget_joke_by_id_func(999)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_parse_error(self):
        """Test parse error propagation."""
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.side_effect = JokeAPIParseError("Malformed response")

            with pytest.raises(JokeAPIParseError):
                await _tool_aget_joke_by_id_func(1)

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_id_boundary_values(self):
        """Test boundary ID values (1 and 451)."""
        # Test ID 1
        joke1 = Joke(id=1, type="general", setup="First", punchline="Joke")
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.return_value = joke1
            result1 = await _tool_aget_joke_by_id_func(1)
            assert "First" in result1

        # Test ID 451
        joke451 = Joke(id=451, type="general", setup="Last", punchline="Joke")
        with patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id:
            mock_aget_by_id.return_value = joke451
            result451 = await _tool_aget_joke_by_id_func(451)
            assert "Last" in result451


class TestToolAgetJokeByType:
    """Tests for tool_aget_joke_by_type() async MCP tool."""

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_general(self):
        """Test getting jokes by 'general' type."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="general", setup="General Setup", punchline="General Punchline"),
            Joke(id=2, type="general", setup="Another Setup", punchline="Another Punchline"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("general")

            assert isinstance(result, str)
            # Should return the first joke formatted
            assert "General Setup" in result
            assert "General Punchline" in result
            mock_aget_by_type.assert_called_once_with("general")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_programming(self):
        """Test getting jokes by 'programming' type."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="programming", setup="Why do programmers prefer dark mode?", punchline="Because light attracts bugs!"),
            Joke(id=2, type="programming", setup="Another code joke", punchline="Another punchline"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("programming")

            assert "Why do programmers prefer dark mode?" in result
            assert "Because light attracts bugs!" in result
            mock_aget_by_type.assert_called_once_with("programming")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_knock_knock(self):
        """Test getting jokes by 'knock-knock' type."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="knock-knock", setup="Knock knock", punchline="Who's there?"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("knock-knock")

            assert "Knock knock" in result
            mock_aget_by_type.assert_called_once_with("knock-knock")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_dad(self):
        """Test getting jokes by 'dad' type."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="dad", setup="I'm afraid for the calendar", punchline="Its days are numbered"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("dad")

            assert "I'm afraid for the calendar" in result
            assert "Its days are numbered" in result
            mock_aget_by_type.assert_called_once_with("dad")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_returns_first_joke(self):
        """Test that the tool returns only the first joke from the collection."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="general", setup="First Setup", punchline="First Punchline"),
            Joke(id=2, type="general", setup="Second Setup", punchline="Second Punchline"),
            Joke(id=3, type="general", setup="Third Setup", punchline="Third Punchline"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("general")

            # Should only contain the first joke
            assert "First Setup" in result
            assert "First Punchline" in result
            # Should NOT contain second or third jokes
            assert "Second Setup" not in result
            assert "Third Setup" not in result

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_format(self):
        """Test that the tool returns properly formatted joke string."""
        jokes = Jokes(jokes=[
            Joke(id=1, type="general", setup="Test Setup", punchline="Test Punchline"),
        ])

        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.return_value = jokes

            result = await _tool_aget_joke_by_type_func("general")

            lines = result.split('\n')
            assert len(lines) >= 2
            assert "Test Setup" in result
            assert "Test Punchline" in result

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_timeout_error(self):
        """Test timeout error propagation."""
        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.side_effect = JokeAPITimeoutError()

            with pytest.raises(JokeAPITimeoutError):
                await _tool_aget_joke_by_type_func("general")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_connection_error(self):
        """Test connection error propagation."""
        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.side_effect = JokeAPIConnectionError()

            with pytest.raises(JokeAPIConnectionError):
                await _tool_aget_joke_by_type_func("programming")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_http_error(self):
        """Test HTTP error propagation."""
        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.side_effect = JokeAPIHTTPError(
                message="Bad request",
                status_code=400,
                response_text="Invalid type"
            )

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await _tool_aget_joke_by_type_func("invalid_type")

            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_parse_error(self):
        """Test parse error propagation."""
        with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
            mock_aget_by_type.side_effect = JokeAPIParseError("Invalid response format")

            with pytest.raises(JokeAPIParseError):
                await _tool_aget_joke_by_type_func("general")

    @pytest.mark.asyncio
    async def test_tool_aget_joke_by_type_all_valid_types(self):
        """Test all valid joke types."""
        valid_types = ["general", "programming", "knock-knock", "dad"]

        for joke_type in valid_types:
            jokes = Jokes(jokes=[
                Joke(id=1, type=joke_type, setup=f"{joke_type} setup", punchline=f"{joke_type} punchline"),
            ])

            with patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:
                mock_aget_by_type.return_value = jokes

                result = await _tool_aget_joke_by_type_func(joke_type)

                assert f"{joke_type} setup" in result
                assert f"{joke_type} punchline" in result
                mock_aget_by_type.assert_called_once_with(joke_type)


class TestAsyncToolsIntegration:
    """Integration tests for async MCP tools."""

    @pytest.mark.asyncio
    async def test_concurrent_async_tool_calls(self):
        """Test multiple async tools called concurrently."""
        import asyncio

        joke1 = Joke(id=1, type="general", setup="Setup 1", punchline="Punchline 1")
        joke2 = Joke(id=2, type="general", setup="Setup 2", punchline="Punchline 2")
        jokes = Jokes(jokes=[Joke(id=3, type="general", setup="Setup 3", punchline="Punchline 3")])

        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget, \
             patch('main.api_aget_joke_by_id', new_callable=AsyncMock) as mock_aget_by_id, \
             patch('main.api_aget_jokes_by_type', new_callable=AsyncMock) as mock_aget_by_type:

            mock_aget.return_value = joke1
            mock_aget_by_id.return_value = joke2
            mock_aget_by_type.return_value = jokes

            # Call all async tools concurrently
            results = await asyncio.gather(
                _tool_aget_joke_func(),
                _tool_aget_joke_by_id_func(42),
                _tool_aget_joke_by_type_func("general"),
            )

            assert len(results) == 3
            assert "Setup 1" in results[0]
            assert "Setup 2" in results[1]
            assert "Setup 3" in results[2]

    @pytest.mark.asyncio
    async def test_sequential_async_tool_calls(self):
        """Test multiple async tools called sequentially."""
        jokes_list = [
            Joke(id=i, type="general", setup=f"Setup {i}", punchline=f"Punchline {i}")
            for i in range(1, 4)
        ]

        with patch('main.api_aget_joke', new_callable=AsyncMock) as mock_aget:
            mock_aget.side_effect = jokes_list

            result1 = await _tool_aget_joke_func()
            result2 = await _tool_aget_joke_func()
            result3 = await _tool_aget_joke_func()

            assert "Setup 1" in result1
            assert "Setup 2" in result2
            assert "Setup 3" in result3
            assert mock_aget.call_count == 3
