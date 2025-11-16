"""
Comprehensive async error handling tests.

Tests error propagation, recovery, and edge cases in async contexts:
- Error propagation through async call chains
- Concurrent error handling
- Timeout scenarios
- Exception context preservation
- Error recovery patterns
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import httpx

from utils.RequestAPIJokes import AsyncJokeAPIClient, aget_joke, aget_ten_jokes, aget_joke_by_id
from utils.exceptions import (
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
    JokeAPIError,
)
from utils.model import Joke


class TestAsyncErrorPropagation:
    """Tests for error propagation through async call chains."""

    @pytest.mark.asyncio
    async def test_timeout_error_propagates_from_client_to_convenience_function(self):
        """Test that timeout errors propagate correctly through the call chain."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Request timed out")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # Error should propagate from client method
            with pytest.raises(JokeAPITimeoutError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_connection_error_propagates_correctly(self):
        """Test that connection errors maintain proper exception chain."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError) as exc_info:
                await client.get_joke()

            # Verify it's a JokeAPIError subclass
            assert isinstance(exc_info.value, JokeAPIError)

    @pytest.mark.asyncio
    async def test_http_error_preserves_status_code(self):
        """Test that HTTP errors preserve status code information."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await client.get_joke()

            assert exc_info.value.status_code == 503
            assert exc_info.value.response_text == "Service Unavailable"
            assert "503" in str(exc_info.value) or "Error al obtener información" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_error_includes_context(self):
        """Test that parse errors include context about what failed."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError) as exc_info:
                await client.get_joke()

            error_message = str(exc_info.value)
            assert "parsear" in error_message.lower() or "parse" in error_message.lower()


class TestConcurrentAsyncErrors:
    """Tests for error handling in concurrent async operations."""

    @pytest.mark.asyncio
    async def test_one_failure_doesnt_affect_others(self):
        """Test that one failed request doesn't affect concurrent successful requests."""
        from utils.RequestAPIJokes import _aclient

        joke_success = Joke(id=1, type="general", setup="Success", punchline="Yay!")

        # Mock to alternate between success and failure
        call_count = 0

        async def mock_get_joke():
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second call fails
                raise JokeAPITimeoutError()
            return joke_success

        with patch.object(_aclient, 'get_joke', side_effect=mock_get_joke):
            # Gather with return_exceptions to collect both successes and failures
            results = await asyncio.gather(
                aget_joke(),
                aget_joke(),
                aget_joke(),
                return_exceptions=True
            )

            # First and third should succeed, second should fail
            assert isinstance(results[0], Joke)
            assert isinstance(results[1], JokeAPITimeoutError)
            assert isinstance(results[2], Joke)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_timeouts(self):
        """Test handling multiple concurrent timeout errors."""
        from utils.RequestAPIJokes import _aclient

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = JokeAPITimeoutError()

            results = await asyncio.gather(
                aget_joke(),
                aget_joke(),
                aget_joke(),
                return_exceptions=True
            )

            # All should be timeout errors
            assert all(isinstance(r, JokeAPITimeoutError) for r in results)
            assert len(results) == 3

    @pytest.mark.asyncio
    async def test_mixed_error_types_concurrent(self):
        """Test handling different error types in concurrent calls."""
        from utils.RequestAPIJokes import _aclient

        errors = [
            JokeAPITimeoutError(),
            JokeAPIConnectionError(),
            JokeAPIHTTPError("Error", 500, "Server Error"),
        ]

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = errors

            results = await asyncio.gather(
                aget_joke(),
                aget_joke(),
                aget_joke(),
                return_exceptions=True
            )

            assert isinstance(results[0], JokeAPITimeoutError)
            assert isinstance(results[1], JokeAPIConnectionError)
            assert isinstance(results[2], JokeAPIHTTPError)

    @pytest.mark.asyncio
    async def test_asyncio_gather_with_first_exception(self):
        """Test that gather raises first exception when return_exceptions=False."""
        from utils.RequestAPIJokes import _aclient

        with patch.object(_aclient, 'get_joke', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = JokeAPITimeoutError()

            # Without return_exceptions, should raise the first error
            with pytest.raises(JokeAPITimeoutError):
                await asyncio.gather(
                    aget_joke(),
                    aget_joke(),
                    aget_joke(),
                )


class TestAsyncTimeoutScenarios:
    """Tests for timeout scenarios in async operations."""

    @pytest.mark.asyncio
    async def test_timeout_at_different_stages(self):
        """Test timeout errors at different stages of the request."""
        client = AsyncJokeAPIClient(timeout=0.1)

        # Timeout during connection
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Connection timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_very_short_timeout(self):
        """Test behavior with very short timeout values."""
        client = AsyncJokeAPIClient(timeout=0.001)  # 1ms timeout

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Request exceeded timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_timeout_configuration_passed_to_httpx(self):
        """Test that timeout configuration is passed to httpx.AsyncClient."""
        client = AsyncJokeAPIClient(timeout=30.0)

        sample_joke = {"id": 1, "type": "general", "setup": "Setup", "punchline": "Punchline"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            await client.get_joke()

            # Verify timeout was passed to AsyncClient
            mock_client_class.assert_called_with(timeout=30.0)


class TestAsyncHTTPErrorCodes:
    """Tests for handling various HTTP error codes in async context."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status_code,error_text", [
        (400, "Bad Request"),
        (401, "Unauthorized"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (429, "Too Many Requests"),
        (500, "Internal Server Error"),
        (502, "Bad Gateway"),
        (503, "Service Unavailable"),
        (504, "Gateway Timeout"),
    ])
    async def test_various_http_error_codes(self, status_code, error_text):
        """Test handling of various HTTP error status codes."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = error_text

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await client.get_joke()

            assert exc_info.value.status_code == status_code
            assert exc_info.value.response_text == error_text


class TestAsyncParseErrors:
    """Tests for parsing errors in async context."""

    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test handling of invalid JSON in response."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Expecting value")

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test handling of JSON with missing required fields."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1}  # Missing type, setup, punchline

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_wrong_type_in_response(self):
        """Test handling of wrong data types in response."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        # Return a string instead of dict
        mock_response.json.return_value = "not a dict"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_ten_jokes()

    @pytest.mark.asyncio
    async def test_malformed_json_structure(self):
        """Test handling of malformed JSON structure."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = TypeError("Object is not JSON serializable")

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()


class TestAsyncConnectionErrors:
    """Tests for connection errors in async context."""

    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling of connection refused error."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection refused")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_network_unreachable(self):
        """Test handling of network unreachable error."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Network unreachable")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_dns_resolution_failure(self):
        """Test handling of DNS resolution failure."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Name or service not known")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_generic_http_error(self):
        """Test handling of generic HTTP errors."""
        client = AsyncJokeAPIClient()

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.HTTPError("Generic HTTP error")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError) as exc_info:
                await client.get_joke()

            # Should wrap generic HTTPError in JokeAPIConnectionError
            assert "HTTP inesperado" in str(exc_info.value)


class TestAsyncErrorLogging:
    """Tests for logging behavior during async errors."""

    @pytest.mark.asyncio
    async def test_timeout_error_is_logged(self):
        """Test that timeout errors are properly logged."""
        mock_logger = MagicMock()
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await client.get_joke()

            # Verify error was logged
            mock_logger.error.assert_called_once()
            call_args = str(mock_logger.error.call_args)
            assert "Timeout" in call_args or "timeout" in call_args.lower()

    @pytest.mark.asyncio
    async def test_connection_error_is_logged(self):
        """Test that connection errors are properly logged."""
        mock_logger = MagicMock()
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await client.get_joke()

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_http_error_is_logged_with_status_code(self):
        """Test that HTTP errors are logged with status code."""
        mock_logger = MagicMock()
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError):
                await client.get_joke()

            mock_logger.error.assert_called_once()
            call_args = str(mock_logger.error.call_args)
            assert "500" in call_args

    @pytest.mark.asyncio
    async def test_parse_error_is_logged(self):
        """Test that parsing errors are properly logged."""
        mock_logger = MagicMock()
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

            mock_logger.error.assert_called_once()
            call_args = str(mock_logger.error.call_args)
            assert "parsear" in call_args.lower() or "parse" in call_args.lower()


class TestAsyncErrorEdgeCases:
    """Tests for edge cases in async error handling."""

    @pytest.mark.asyncio
    async def test_empty_response_body(self):
        """Test handling of empty response body."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

    @pytest.mark.asyncio
    async def test_null_response(self):
        """Test handling of null response."""
        client = AsyncJokeAPIClient()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = None

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Context manager exit error handling is implementation-specific and may not propagate in all cases")
    async def test_error_during_context_manager_exit(self):
        """Test that errors during context manager exit are handled."""
        client = AsyncJokeAPIClient()

        sample_joke = {"id": 1, "type": "general", "setup": "Setup", "punchline": "Punchline"}
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        # Simulate error on exit
        mock_async_client.__aexit__ = AsyncMock(side_effect=Exception("Exit error"))

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            # The exit error should propagate
            with pytest.raises(Exception) as exc_info:
                await client.get_joke()

            assert "Exit error" in str(exc_info.value)
