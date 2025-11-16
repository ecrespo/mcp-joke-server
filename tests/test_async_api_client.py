"""
Comprehensive unit tests for AsyncJokeAPIClient.

Tests the asynchronous API client implementation including:
- Basic async method functionality
- Exception handling (timeout, connection, HTTP, parsing errors)
- Response parsing correctness
- httpx.AsyncClient interaction
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from utils.RequestAPIJokes import AsyncJokeAPIClient
from utils.model import Joke, Jokes
from utils.exceptions import (
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
)


@pytest.fixture
def async_client():
    """Fixture providing a fresh AsyncJokeAPIClient instance."""
    return AsyncJokeAPIClient(base_url="https://api.test.com", timeout=5.0)


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    logger = MagicMock()
    logger.error = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    return logger


@pytest.fixture
def sample_joke_data():
    """Fixture providing sample joke data."""
    return {
        "id": 1,
        "type": "general",
        "setup": "Why did the chicken cross the road?",
        "punchline": "To get to the other side!"
    }


@pytest.fixture
def sample_ten_jokes_data():
    """Fixture providing sample data for 10 jokes."""
    return [
        {
            "id": i,
            "type": "general",
            "setup": f"Setup {i}",
            "punchline": f"Punchline {i}"
        }
        for i in range(1, 11)
    ]


class TestAsyncJokeAPIClientInitialization:
    """Tests for AsyncJokeAPIClient initialization."""

    def test_init_default_parameters(self):
        """Test client initialization with default parameters."""
        client = AsyncJokeAPIClient()
        assert client.base_url == "https://official-joke-api.appspot.com"
        assert client.timeout == 10
        assert client._log is not None

    def test_init_custom_parameters(self, mock_logger):
        """Test client initialization with custom parameters."""
        client = AsyncJokeAPIClient(
            base_url="https://custom.api.com",
            timeout=15.0,
            logger=mock_logger
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 15
        assert client._log == mock_logger


class TestAsyncJokeAPIClientGetJoke:
    """Tests for AsyncJokeAPIClient.get_joke() method."""

    @pytest.mark.asyncio
    async def test_get_joke_success(self, async_client, sample_joke_data):
        """Test successful joke retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_joke()

            assert isinstance(result, Joke)
            assert result.id == 1
            assert result.type == "general"
            assert result.setup == "Why did the chicken cross the road?"
            assert result.punchline == "To get to the other side!"
            mock_async_client.get.assert_called_once_with("https://api.test.com/random_joke")

    @pytest.mark.asyncio
    async def test_get_joke_timeout_error(self, async_client):
        """Test timeout error handling."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await async_client.get_joke()

    @pytest.mark.asyncio
    async def test_get_joke_connection_error(self, async_client):
        """Test connection error handling."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await async_client.get_joke()

    @pytest.mark.asyncio
    async def test_get_joke_http_error(self, async_client):
        """Test HTTP error handling (non-200 status)."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await async_client.get_joke()

            assert exc_info.value.status_code == 404
            assert exc_info.value.response_text == "Not Found"

    @pytest.mark.asyncio
    async def test_get_joke_parse_error(self, async_client):
        """Test parsing error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}  # Missing required fields

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await async_client.get_joke()

    @pytest.mark.asyncio
    async def test_get_joke_generic_http_error(self, async_client):
        """Test generic HTTP error handling."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.HTTPError("Generic HTTP error")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await async_client.get_joke()


class TestAsyncJokeAPIClientGetTenJokes:
    """Tests for AsyncJokeAPIClient.get_ten_jokes() method."""

    @pytest.mark.asyncio
    async def test_get_ten_jokes_success(self, async_client, sample_ten_jokes_data):
        """Test successful retrieval of ten jokes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_ten_jokes_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_ten_jokes()

            assert isinstance(result, Jokes)
            assert len(result.jokes) == 10
            assert all(isinstance(joke, Joke) for joke in result.jokes)
            assert result.jokes[0].id == 1
            assert result.jokes[9].id == 10
            mock_async_client.get.assert_called_once_with("https://api.test.com/random_ten")

    @pytest.mark.asyncio
    async def test_get_ten_jokes_timeout(self, async_client):
        """Test timeout error when getting ten jokes."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await async_client.get_ten_jokes()

    @pytest.mark.asyncio
    async def test_get_ten_jokes_connection_error(self, async_client):
        """Test connection error when getting ten jokes."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await async_client.get_ten_jokes()

    @pytest.mark.asyncio
    async def test_get_ten_jokes_http_error_500(self, async_client):
        """Test HTTP 500 error when getting ten jokes."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await async_client.get_ten_jokes()

            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_ten_jokes_invalid_response_format(self, async_client):
        """Test parsing error with invalid response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"not": "a list"}  # Should be a list

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await async_client.get_ten_jokes()


class TestAsyncJokeAPIClientGetJokeById:
    """Tests for AsyncJokeAPIClient.get_joke_by_id() method."""

    @pytest.mark.asyncio
    async def test_get_joke_by_id_success(self, async_client, sample_joke_data):
        """Test successful joke retrieval by ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_joke_by_id(1)

            assert isinstance(result, Joke)
            assert result.id == 1
            mock_async_client.get.assert_called_once_with("https://api.test.com/jokes/1")

    @pytest.mark.asyncio
    async def test_get_joke_by_id_various_ids(self, async_client, sample_joke_data):
        """Test joke retrieval with different IDs."""
        for joke_id in [1, 100, 451]:
            mock_response = MagicMock()
            mock_response.status_code = 200
            sample_joke_data["id"] = joke_id
            mock_response.json.return_value = sample_joke_data

            mock_async_client = AsyncMock()
            mock_async_client.get.return_value = mock_response

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client_class.return_value.__aenter__.return_value = mock_async_client

                result = await async_client.get_joke_by_id(joke_id)

                assert result.id == joke_id
                mock_async_client.get.assert_called_once_with(f"https://api.test.com/jokes/{joke_id}")

    @pytest.mark.asyncio
    async def test_get_joke_by_id_not_found(self, async_client):
        """Test 404 error when joke ID doesn't exist."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Joke not found"

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIHTTPError) as exc_info:
                await async_client.get_joke_by_id(999)

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_joke_by_id_timeout(self, async_client):
        """Test timeout when getting joke by ID."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await async_client.get_joke_by_id(1)


class TestAsyncJokeAPIClientGetJokesByType:
    """Tests for AsyncJokeAPIClient.get_jokes_by_type() method."""

    @pytest.mark.asyncio
    async def test_get_jokes_by_type_general(self, async_client, sample_ten_jokes_data):
        """Test getting jokes by 'general' type."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_ten_jokes_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_jokes_by_type("general")

            assert isinstance(result, Jokes)
            assert len(result.jokes) == 10
            mock_async_client.get.assert_called_once_with("https://api.test.com/jokes/general/random")

    @pytest.mark.asyncio
    async def test_get_jokes_by_type_programming(self, async_client, sample_ten_jokes_data):
        """Test getting jokes by 'programming' type."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        for joke in sample_ten_jokes_data:
            joke["type"] = "programming"
        mock_response.json.return_value = sample_ten_jokes_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_jokes_by_type("programming")

            assert isinstance(result, Jokes)
            assert all(joke.type == "programming" for joke in result.jokes)
            mock_async_client.get.assert_called_once_with("https://api.test.com/jokes/programming/random")

    @pytest.mark.asyncio
    async def test_get_jokes_by_type_knock_knock(self, async_client, sample_ten_jokes_data):
        """Test getting jokes by 'knock-knock' type."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        for joke in sample_ten_jokes_data:
            joke["type"] = "knock-knock"
        mock_response.json.return_value = sample_ten_jokes_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            result = await async_client.get_jokes_by_type("knock-knock")

            assert isinstance(result, Jokes)
            mock_async_client.get.assert_called_once_with("https://api.test.com/jokes/knock-knock/random")

    @pytest.mark.asyncio
    async def test_get_jokes_by_type_timeout(self, async_client):
        """Test timeout when getting jokes by type."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await async_client.get_jokes_by_type("general")

    @pytest.mark.asyncio
    async def test_get_jokes_by_type_connection_error(self, async_client):
        """Test connection error when getting jokes by type."""
        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await async_client.get_jokes_by_type("programming")


class TestAsyncJokeAPIClientContextManager:
    """Tests for httpx.AsyncClient context manager usage."""

    @pytest.mark.asyncio
    async def test_async_client_context_manager_cleanup(self, async_client, sample_joke_data):
        """Test that AsyncClient context manager is properly used."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response
        mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
        mock_async_client.__aexit__ = AsyncMock(return_value=None)

        with patch('httpx.AsyncClient', return_value=mock_async_client):
            await async_client.get_joke()

            # Verify context manager was entered and exited
            mock_async_client.__aenter__.assert_called_once()
            mock_async_client.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, sample_joke_data):
        """Test that timeout is properly configured in AsyncClient."""
        client = AsyncJokeAPIClient(timeout=20.0)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_joke_data

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            await client.get_joke()

            # Verify AsyncClient was initialized with correct timeout
            mock_client_class.assert_called_once_with(timeout=20.0)


class TestAsyncJokeAPIClientLogging:
    """Tests for logging behavior in AsyncJokeAPIClient."""

    @pytest.mark.asyncio
    async def test_logging_on_timeout(self, mock_logger):
        """Test that timeout errors are logged."""
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ReadTimeout("Timeout")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPITimeoutError):
                await client.get_joke()

            mock_logger.error.assert_called_once()
            assert "Timeout" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_logging_on_connection_error(self, mock_logger):
        """Test that connection errors are logged."""
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_async_client = AsyncMock()
        mock_async_client.get.side_effect = httpx.ConnectError("Connection failed")

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIConnectionError):
                await client.get_joke()

            mock_logger.error.assert_called_once()
            assert "conexión" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_logging_on_http_error(self, mock_logger):
        """Test that HTTP errors are logged."""
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
            assert "500" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_logging_on_parse_error(self, mock_logger):
        """Test that parsing errors are logged."""
        client = AsyncJokeAPIClient(logger=mock_logger)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "data"}

        mock_async_client = AsyncMock()
        mock_async_client.get.return_value = mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client_class.return_value.__aenter__.return_value = mock_async_client

            with pytest.raises(JokeAPIParseError):
                await client.get_joke()

            mock_logger.error.assert_called_once()
            assert "parsear" in str(mock_logger.error.call_args)
