"""
Async integration tests.

End-to-end tests for async functionality:
- Full async flow from tools to API client
- Integration between different async components
- Real-world usage scenarios
- Performance characteristics
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from main import tool_aget_joke, tool_aget_joke_by_id, tool_aget_joke_by_type
from utils.RequestAPIJokes import (
    AsyncJokeAPIClient,
    aget_joke,
    aget_ten_jokes,
    aget_joke_by_id,
    aget_jokes_by_type,
)
from utils.model import Joke, Jokes
from utils.exceptions import JokeAPITimeoutError, JokeAPIHTTPError


# Access the underlying functions from the decorated tools
_tool_aget_joke_func = tool_aget_joke.fn if hasattr(tool_aget_joke, 'fn') else tool_aget_joke
_tool_aget_joke_by_id_func = tool_aget_joke_by_id.fn if hasattr(tool_aget_joke_by_id, 'fn') else tool_aget_joke_by_id
_tool_aget_joke_by_type_func = tool_aget_joke_by_type.fn if hasattr(tool_aget_joke_by_type, 'fn') else tool_aget_joke_by_type


@pytest.fixture
def mock_httpx_response():
    """Factory for creating mock httpx responses."""
    def _create_response(data, status_code=200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = data
        response.text = str(data)
        return response
    return _create_response


@pytest.fixture
def sample_joke_data():
    """Sample joke data."""
    return {
        "id": 123,
        "type": "programming",
        "setup": "Why do programmers prefer dark mode?",
        "punchline": "Because light attracts bugs!"
    }


@pytest.fixture
def sample_jokes_data():
    """Sample jokes collection data."""
    return [
        {
            "id": i,
            "type": "general",
            "setup": f"Why did the {i} cross the road?",
            "punchline": f"To get to joke {i}!"
        }
        for i in range(1, 11)
    ]


class TestAsyncEndToEndFlow:
    """End-to-end tests for complete async flow."""

    @pytest.mark.asyncio
    async def test_full_flow_client_to_tool(self, mock_httpx_response, sample_joke_data):
        """Test complete flow from AsyncJokeAPIClient to MCP tool."""
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Call the tool which internally uses the client
            result = await _tool_aget_joke_func()

            # Verify the complete flow worked
            assert isinstance(result, str)
            assert "Why do programmers prefer dark mode?" in result
            assert "Because light attracts bugs!" in result
            mock_async_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_flow_with_id_parameter(self, mock_httpx_response, sample_joke_data):
        """Test complete flow with ID parameter passing."""
        sample_joke_data["id"] = 42
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await _tool_aget_joke_by_id_func(42)

            assert isinstance(result, str)
            assert "Why do programmers prefer dark mode?" in result
            # Verify correct endpoint was called
            call_args = mock_async_client.get.call_args[0][0]
            assert "/jokes/42" in call_args

    @pytest.mark.asyncio
    async def test_full_flow_with_type_parameter(self, mock_httpx_response, sample_jokes_data):
        """Test complete flow with type parameter."""
        # Modify data to be programming type
        for joke in sample_jokes_data:
            joke["type"] = "programming"

        mock_response = mock_httpx_response(sample_jokes_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await _tool_aget_joke_by_type_func("programming")

            assert isinstance(result, str)
            # Should return first joke from the collection
            assert "Why did the 1 cross the road?" in result
            # Verify correct endpoint was called
            call_args = mock_async_client.get.call_args[0][0]
            assert "/jokes/programming/random" in call_args


class TestAsyncConvenienceFunctionsIntegration:
    """Integration tests for async convenience functions."""

    @pytest.mark.asyncio
    async def test_aget_joke_full_integration(self, mock_httpx_response, sample_joke_data):
        """Test aget_joke full integration."""
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            joke = await aget_joke()

            assert isinstance(joke, Joke)
            assert joke.id == 123
            assert joke.type == "programming"
            assert joke.setup == "Why do programmers prefer dark mode?"
            assert joke.punchline == "Because light attracts bugs!"

    @pytest.mark.asyncio
    async def test_aget_ten_jokes_full_integration(self, mock_httpx_response, sample_jokes_data):
        """Test aget_ten_jokes full integration."""
        mock_response = mock_httpx_response(sample_jokes_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            jokes = await aget_ten_jokes()

            assert isinstance(jokes, Jokes)
            assert len(jokes.jokes) == 10
            assert all(isinstance(j, Joke) for j in jokes.jokes)
            assert jokes.jokes[0].id == 1
            assert jokes.jokes[9].id == 10

    @pytest.mark.asyncio
    async def test_aget_joke_by_id_full_integration(self, mock_httpx_response, sample_joke_data):
        """Test aget_joke_by_id full integration."""
        sample_joke_data["id"] = 250
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            joke = await aget_joke_by_id(250)

            assert isinstance(joke, Joke)
            assert joke.id == 250
            # Verify correct URL was called
            call_args = mock_async_client.get.call_args[0][0]
            assert "/jokes/250" in call_args

    @pytest.mark.asyncio
    async def test_aget_jokes_by_type_full_integration(self, mock_httpx_response, sample_jokes_data):
        """Test aget_jokes_by_type full integration."""
        for joke in sample_jokes_data:
            joke["type"] = "knock-knock"

        mock_response = mock_httpx_response(sample_jokes_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            jokes = await aget_jokes_by_type("knock-knock")

            assert isinstance(jokes, Jokes)
            assert all(j.type == "knock-knock" for j in jokes.jokes)
            # Verify correct URL was called
            call_args = mock_async_client.get.call_args[0][0]
            assert "/jokes/knock-knock/random" in call_args


class TestAsyncMultiLayerIntegration:
    """Tests for integration across multiple layers."""

    @pytest.mark.asyncio
    async def test_error_propagation_through_all_layers(self):
        """Test that errors propagate correctly through all layers."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = JokeAPITimeoutError()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Error should propagate from client -> convenience function -> tool
            with pytest.raises(JokeAPITimeoutError):
                await _tool_aget_joke_func()

    @pytest.mark.asyncio
    async def test_data_transformation_through_layers(self, mock_httpx_response, sample_joke_data):
        """Test data transformation through all layers."""
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Test data flow: dict -> Joke -> formatted string
            joke = await aget_joke()
            assert isinstance(joke, Joke)

            # Now through tool which formats it
            formatted = await _tool_aget_joke_func()
            assert isinstance(formatted, str)
            assert joke.setup in formatted
            assert joke.punchline in formatted


class TestAsyncRealWorldScenarios:
    """Tests simulating real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_sequential_requests_different_endpoints(self, mock_httpx_response):
        """Test sequential requests to different endpoints."""
        joke_data = {
            "id": 1,
            "type": "general",
            "setup": "Setup",
            "punchline": "Punchline"
        }
        jokes_data = [joke_data.copy() for _ in range(10)]

        mock_responses = [
            mock_httpx_response(joke_data),
            mock_httpx_response(jokes_data),
            mock_httpx_response(joke_data),
        ]

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = mock_responses

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Sequential calls to different endpoints
            joke1 = await aget_joke()
            jokes = await aget_ten_jokes()
            joke2 = await aget_joke_by_id(42)

            assert isinstance(joke1, Joke)
            assert isinstance(jokes, Jokes)
            assert isinstance(joke2, Joke)
            assert mock_async_client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_concurrent_requests_same_endpoint(self, mock_httpx_response, sample_joke_data):
        """Test concurrent requests to the same endpoint."""
        # Create different jokes for each request
        jokes = [
            {"id": i, "type": "general", "setup": f"Setup {i}", "punchline": f"Punchline {i}"}
            for i in range(1, 6)
        ]

        mock_responses = [mock_httpx_response(joke) for joke in jokes]
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = mock_responses

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Make 5 concurrent requests
            results = await asyncio.gather(*[aget_joke() for _ in range(5)])

            assert len(results) == 5
            assert all(isinstance(r, Joke) for r in results)
            # Each should have different ID
            ids = [r.id for r in results]
            assert ids == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_scenario(self, mock_httpx_response, sample_joke_data):
        """Test scenario with both successful and failed requests."""
        success_response = mock_httpx_response(sample_joke_data)
        error_response = mock_httpx_response({}, status_code=500)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = [
            success_response,
            error_response,
            success_response,
        ]

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # First should succeed
            joke1 = await aget_joke()
            assert isinstance(joke1, Joke)

            # Second should fail
            with pytest.raises(JokeAPIHTTPError):
                await aget_joke()

            # Third should succeed
            joke3 = await aget_joke()
            assert isinstance(joke3, Joke)

    @pytest.mark.asyncio
    async def test_retry_after_failure_scenario(self, mock_httpx_response, sample_joke_data):
        """Test retry scenario after initial failure."""
        error_response = mock_httpx_response({}, status_code=503)
        success_response = mock_httpx_response(sample_joke_data)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = [error_response, success_response]

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # First attempt fails
            with pytest.raises(JokeAPIHTTPError):
                await aget_joke()

            # Retry succeeds
            joke = await aget_joke()
            assert isinstance(joke, Joke)

    @pytest.mark.asyncio
    async def test_all_joke_types_in_sequence(self, mock_httpx_response):
        """Test fetching all joke types in sequence."""
        types = ["general", "programming", "knock-knock", "dad"]
        jokes_data_by_type = {
            joke_type: [
                {"id": i, "type": joke_type, "setup": f"{joke_type} setup {i}", "punchline": f"punchline {i}"}
                for i in range(1, 4)
            ]
            for joke_type in types
        }

        mock_responses = [mock_httpx_response(jokes_data_by_type[t]) for t in types]
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = mock_responses

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Fetch all types
            results = {}
            for joke_type in types:
                results[joke_type] = await aget_jokes_by_type(joke_type)

            # Verify all were fetched correctly
            for joke_type in types:
                assert isinstance(results[joke_type], Jokes)
                assert all(j.type == joke_type for j in results[joke_type].jokes)


class TestAsyncPerformanceCharacteristics:
    """Tests for performance characteristics of async operations."""

    @pytest.mark.asyncio
    async def test_concurrent_faster_than_sequential(self, mock_httpx_response, sample_joke_data):
        """Test that concurrent requests are faster than sequential."""
        import time

        # Simulate slow responses
        async def slow_get(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            return mock_httpx_response(sample_joke_data)

        mock_async_client = AsyncMock()
        mock_async_client.get = slow_get

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Concurrent execution
            start_concurrent = time.time()
            await asyncio.gather(*[aget_joke() for _ in range(5)])
            concurrent_time = time.time() - start_concurrent

            # Sequential execution
            start_sequential = time.time()
            for _ in range(5):
                await aget_joke()
            sequential_time = time.time() - start_sequential

            # Concurrent should be significantly faster
            # With 5 requests of 100ms each:
            # Sequential: ~500ms, Concurrent: ~100ms
            assert concurrent_time < sequential_time * 0.5

    @pytest.mark.asyncio
    async def test_many_concurrent_requests(self, mock_httpx_response, sample_joke_data):
        """Test handling many concurrent requests."""
        num_requests = 50

        mock_responses = [mock_httpx_response(sample_joke_data) for _ in range(num_requests)]
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = mock_responses

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            results = await asyncio.gather(*[aget_joke() for _ in range(num_requests)])

            assert len(results) == num_requests
            assert all(isinstance(r, Joke) for r in results)


class TestAsyncClientLifecycle:
    """Tests for async client lifecycle management."""

    @pytest.mark.asyncio
    async def test_client_context_manager_properly_closes(self, mock_httpx_response, sample_joke_data):
        """Test that AsyncClient context manager properly closes."""
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock()

        with patch('httpx.AsyncClient', return_value=mock_async_client):
            await aget_joke()

            # Verify context manager was entered and exited
            mock_async_client.__aenter__.assert_called()
            mock_async_client.__aexit__.assert_called()

    @pytest.mark.asyncio
    async def test_multiple_requests_create_separate_clients(self, mock_httpx_response, sample_joke_data):
        """Test that each request creates its own client instance."""
        mock_response = mock_httpx_response(sample_joke_data)
        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Make multiple requests
            await aget_joke()
            await aget_joke()
            await aget_joke()

            # Each request should create a new AsyncClient
            assert mock_client_class.call_count == 3
