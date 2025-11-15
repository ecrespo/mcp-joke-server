"""
Unit tests for utils/exceptions.py

Tests for custom exceptions used by the Joke API client.
"""

import pytest
from utils.exceptions import (
    JokeAPIError,
    JokeAPITimeoutError,
    JokeAPIConnectionError,
    JokeAPIHTTPError,
    JokeAPIParseError,
)


class TestJokeAPIError:
    """Tests for JokeAPIError base exception."""

    def test_create_with_message(self):
        """Test creating error with message."""
        error = JokeAPIError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.status_code is None

    def test_create_with_status_code(self):
        """Test creating error with status code."""
        error = JokeAPIError("Test error", status_code=500)
        assert error.message == "Test error"
        assert error.status_code == 500

    def test_is_exception(self):
        """Test that JokeAPIError is an Exception."""
        error = JokeAPIError("Test")
        assert isinstance(error, Exception)


class TestJokeAPITimeoutError:
    """Tests for JokeAPITimeoutError."""

    def test_create_with_default_message(self):
        """Test creating timeout error with default message."""
        error = JokeAPITimeoutError()
        assert "tiempo de espera" in str(error).lower()

    def test_create_with_custom_message(self):
        """Test creating timeout error with custom message."""
        error = JokeAPITimeoutError("Custom timeout message")
        assert str(error) == "Custom timeout message"

    def test_is_subclass_of_base(self):
        """Test that timeout error is subclass of base error."""
        error = JokeAPITimeoutError()
        assert isinstance(error, JokeAPIError)


class TestJokeAPIConnectionError:
    """Tests for JokeAPIConnectionError."""

    def test_create_with_default_message(self):
        """Test creating connection error with default message."""
        error = JokeAPIConnectionError()
        assert "conexión" in str(error).lower()

    def test_create_with_custom_message(self):
        """Test creating connection error with custom message."""
        error = JokeAPIConnectionError("Custom connection message")
        assert str(error) == "Custom connection message"

    def test_is_subclass_of_base(self):
        """Test that connection error is subclass of base error."""
        error = JokeAPIConnectionError()
        assert isinstance(error, JokeAPIError)


class TestJokeAPIHTTPError:
    """Tests for JokeAPIHTTPError."""

    def test_create_with_required_params(self):
        """Test creating HTTP error with required parameters."""
        error = JokeAPIHTTPError(
            message="HTTP Error",
            status_code=404
        )
        assert error.message == "HTTP Error"
        assert error.status_code == 404
        assert error.response_text == ""

    def test_create_with_response_text(self):
        """Test creating HTTP error with response text."""
        error = JokeAPIHTTPError(
            message="Not Found",
            status_code=404,
            response_text="Resource not found"
        )
        assert error.message == "Not Found"
        assert error.status_code == 404
        assert error.response_text == "Resource not found"

    def test_is_subclass_of_base(self):
        """Test that HTTP error is subclass of base error."""
        error = JokeAPIHTTPError("Error", 500)
        assert isinstance(error, JokeAPIError)

    def test_different_status_codes(self):
        """Test creating errors with different status codes."""
        error_404 = JokeAPIHTTPError("Not Found", 404)
        error_500 = JokeAPIHTTPError("Server Error", 500)
        error_503 = JokeAPIHTTPError("Service Unavailable", 503)

        assert error_404.status_code == 404
        assert error_500.status_code == 500
        assert error_503.status_code == 503


class TestJokeAPIParseError:
    """Tests for JokeAPIParseError."""

    def test_create_with_default_message(self):
        """Test creating parse error with default message."""
        error = JokeAPIParseError()
        assert "parsear" in str(error).lower()

    def test_create_with_custom_message(self):
        """Test creating parse error with custom message."""
        error = JokeAPIParseError("Custom parse error")
        assert str(error) == "Custom parse error"

    def test_is_subclass_of_base(self):
        """Test that parse error is subclass of base error."""
        error = JokeAPIParseError()
        assert isinstance(error, JokeAPIError)


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from JokeAPIError."""
        exceptions = [
            JokeAPITimeoutError(),
            JokeAPIConnectionError(),
            JokeAPIHTTPError("msg", 500),
            JokeAPIParseError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, JokeAPIError)
            assert isinstance(exc, Exception)

    def test_can_catch_with_base_exception(self):
        """Test that all exceptions can be caught with base class."""
        def raise_timeout():
            raise JokeAPITimeoutError()

        def raise_connection():
            raise JokeAPIConnectionError()

        def raise_http():
            raise JokeAPIHTTPError("Error", 404)

        def raise_parse():
            raise JokeAPIParseError()

        for func in [raise_timeout, raise_connection, raise_http, raise_parse]:
            with pytest.raises(JokeAPIError):
                func()

    def test_specific_exception_catching(self):
        """Test catching specific exception types."""
        with pytest.raises(JokeAPITimeoutError):
            raise JokeAPITimeoutError()

        with pytest.raises(JokeAPIConnectionError):
            raise JokeAPIConnectionError()

        with pytest.raises(JokeAPIHTTPError):
            raise JokeAPIHTTPError("Error", 404)

        with pytest.raises(JokeAPIParseError):
            raise JokeAPIParseError()
