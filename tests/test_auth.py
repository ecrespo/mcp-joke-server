"""
Tests for authentication utilities (utils/auth.py).

This module tests the LocalTokenValidator and LocalTokenClient classes
that handle token validation and retrieval.
"""

import pytest
from utils.auth import LocalTokenValidator, LocalTokenClient


class TestLocalTokenValidator:
    """Test suite for LocalTokenValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a LocalTokenValidator instance for testing."""
        return LocalTokenValidator()

    def test_validator_initialization(self, validator, valid_auth_token):
        """Test that validator initializes with correct token from settings."""
        assert validator.local_token == valid_auth_token
        assert validator.local_token is not None

    def test_validate_valid_token(self, validator, valid_auth_token):
        """Test validation of a correct token."""
        result = validator.validate_token(valid_auth_token)

        assert result is not None
        assert result["valid"] is True
        assert result["type"] == "local_token"

    def test_validate_invalid_token(self, validator, invalid_auth_token):
        """Test validation of an incorrect token."""
        result = validator.validate_token(invalid_auth_token)

        assert result is None

    def test_validate_empty_token(self, validator):
        """Test validation of an empty token."""
        result = validator.validate_token("")

        assert result is None

    def test_validate_none_token(self, validator):
        """Test validation of None token."""
        result = validator.validate_token(None)

        assert result is None

    def test_validate_whitespace_token(self, validator):
        """Test validation of whitespace-only token."""
        result = validator.validate_token("   ")

        # Whitespace should not match the actual token
        assert result is None

    def test_validate_token_case_sensitive(self, validator, valid_auth_token):
        """Test that token validation is case-sensitive."""
        # Change case of token
        wrong_case_token = valid_auth_token.upper() if valid_auth_token.islower() else valid_auth_token.lower()

        # Only validate if the token actually has different casing
        if wrong_case_token != valid_auth_token:
            result = validator.validate_token(wrong_case_token)
            assert result is None

    def test_validate_token_no_partial_match(self, validator, valid_auth_token):
        """Test that partial tokens don't validate."""
        # Use only part of the token
        if len(valid_auth_token) > 5:
            partial_token = valid_auth_token[:5]
            result = validator.validate_token(partial_token)
            assert result is None

    def test_validate_token_with_extra_chars(self, validator, valid_auth_token):
        """Test that tokens with extra characters don't validate."""
        extra_token = valid_auth_token + "extra"
        result = validator.validate_token(extra_token)

        assert result is None

    def test_validator_handles_exceptions_gracefully(self, validator):
        """Test that validator handles unexpected exceptions."""
        # This should not raise an exception
        result = validator.validate_token(12345)  # Wrong type

        # Should return None instead of crashing
        assert result is None


class TestLocalTokenClient:
    """Test suite for LocalTokenClient class."""

    @pytest.fixture
    def client(self):
        """Create a LocalTokenClient instance for testing."""
        return LocalTokenClient()

    def test_client_initialization(self, client, valid_auth_token):
        """Test that client initializes with correct token from settings."""
        assert client.local_token == valid_auth_token
        assert client.local_token is not None

    def test_get_token_returns_valid_token(self, client, valid_auth_token):
        """Test that get_token returns the configured token."""
        token = client.get_token()

        assert token == valid_auth_token
        assert token is not None

    def test_get_token_returns_string(self, client):
        """Test that get_token returns a string."""
        token = client.get_token()

        assert isinstance(token, str)
        assert len(token) > 0

    def test_get_token_consistent(self, client):
        """Test that get_token returns the same token on multiple calls."""
        token1 = client.get_token()
        token2 = client.get_token()

        assert token1 == token2


class TestAuthIntegration:
    """Integration tests for authentication components."""

    def test_validator_and_client_use_same_token(self):
        """Test that validator and client use the same token from settings."""
        validator = LocalTokenValidator()
        client = LocalTokenClient()

        # Both should have the same token
        assert validator.local_token == client.local_token

    def test_client_token_validates_successfully(self):
        """Test that a token from the client validates successfully."""
        client = LocalTokenClient()
        validator = LocalTokenValidator()

        token = client.get_token()
        result = validator.validate_token(token)

        assert result is not None
        assert result["valid"] is True

    def test_validator_rejects_modified_client_token(self):
        """Test that a modified client token is rejected."""
        client = LocalTokenClient()
        validator = LocalTokenValidator()

        token = client.get_token()
        modified_token = token + "modified"

        result = validator.validate_token(modified_token)

        assert result is None


class TestAuthWithDifferentTokens:
    """Test authentication with various token formats."""

    @pytest.mark.parametrize(
        "test_token",
        [
            "simple-token",
            "token-with-dashes",
            "token_with_underscores",
            "MixedCaseToken123",
            "token.with.dots",
            "very-long-token-" * 10,
            "a",  # Single character
            "-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys",  # URL-safe base64
        ],
    )
    def test_validator_with_various_token_formats(self, test_token, monkeypatch):
        """Test that validator works with various token formats."""
        # Temporarily set the token for this test
        monkeypatch.setenv("LOCAL_TOKEN", test_token)

        # Create new instances to pick up the new environment variable
        from utils.config import Settings

        # Force reload of settings
        Settings._instances.clear()

        validator = LocalTokenValidator()

        # The validator should accept the configured token
        result = validator.validate_token(test_token)
        assert result is not None
        assert result["valid"] is True

        # And reject different tokens
        result = validator.validate_token(test_token + "x")
        assert result is None
