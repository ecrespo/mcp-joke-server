"""
Tests for LocalTokenAuthMiddleware.

This module tests the authentication middleware that validates Bearer tokens
for HTTP and SSE transports while allowing STDIO transport without authentication.
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastmcp.exceptions import ToolError


@pytest.fixture
def auth_middleware():
    """Create an instance of LocalTokenAuthMiddleware for testing."""
    from main import LocalTokenAuthMiddleware

    return LocalTokenAuthMiddleware()


@pytest.mark.asyncio
async def test_middleware_allows_stdio_without_auth(auth_middleware, mock_middleware_context):
    """Test that STDIO transport (no HTTP request) bypasses authentication."""
    # Mock call_next to verify it's called
    call_next = AsyncMock(return_value="success")

    # Mock get_http_request to return None (simulating STDIO transport)
    with patch("main.get_http_request", return_value=None):
        result = await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify call_next was called
    assert result == "success"
    call_next.assert_awaited_once()

    # Verify no state was set (no authentication occurred)
    mock_middleware_context.fastmcp_context.set_state.assert_not_called()


@pytest.mark.asyncio
async def test_middleware_rejects_missing_auth_header(
    auth_middleware, mock_middleware_context, mock_http_request_without_auth
):
    """Test that requests without Authorization header are rejected."""
    call_next = AsyncMock()

    with patch("main.get_http_request", return_value=mock_http_request_without_auth):
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify error message
    assert "Authentication required" in str(exc_info.value)
    assert "Bearer token" in str(exc_info.value)

    # Verify call_next was NOT called
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_middleware_rejects_invalid_auth_format(
    auth_middleware, mock_middleware_context
):
    """Test that requests with invalid Authorization format are rejected."""
    call_next = AsyncMock()

    # Create request with invalid format (missing "Bearer" prefix)
    mock_request = Mock()
    mock_request.headers = {"authorization": "InvalidFormat token123"}

    with patch("main.get_http_request", return_value=mock_request):
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify error message
    assert "Invalid Authorization header format" in str(exc_info.value)
    assert "Bearer" in str(exc_info.value)

    # Verify call_next was NOT called
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_middleware_rejects_invalid_token(
    auth_middleware, mock_middleware_context, mock_http_request_invalid_auth
):
    """Test that requests with invalid tokens are rejected."""
    call_next = AsyncMock()

    with patch("main.get_http_request", return_value=mock_http_request_invalid_auth):
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify error message
    assert "Authentication failed" in str(exc_info.value)
    assert "Invalid or expired token" in str(exc_info.value)

    # Verify call_next was NOT called
    call_next.assert_not_awaited()


@pytest.mark.asyncio
async def test_middleware_accepts_valid_token(
    auth_middleware, mock_middleware_context, mock_http_request_with_auth
):
    """Test that requests with valid tokens are accepted."""
    call_next = AsyncMock(return_value="tool_result")

    with patch("main.get_http_request", return_value=mock_http_request_with_auth):
        result = await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify call_next was called and result was returned
    assert result == "tool_result"
    call_next.assert_awaited_once()

    # Verify authentication state was set
    assert mock_middleware_context.fastmcp_context.set_state.call_count == 2
    mock_middleware_context.fastmcp_context.set_state.assert_any_call(
        "authenticated", True
    )
    mock_middleware_context.fastmcp_context.set_state.assert_any_call(
        "auth_type", "local_token"
    )


@pytest.mark.asyncio
async def test_middleware_handles_bearer_case_insensitive(
    auth_middleware, mock_middleware_context, valid_auth_token
):
    """Test that Bearer prefix is case-insensitive."""
    call_next = AsyncMock(return_value="success")

    # Test with lowercase "bearer"
    mock_request = Mock()
    mock_request.headers = {"authorization": f"bearer {valid_auth_token}"}

    with patch("main.get_http_request", return_value=mock_request):
        result = await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    assert result == "success"
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_middleware_handles_bearer_with_extra_spaces(
    auth_middleware, mock_middleware_context, valid_auth_token
):
    """Test that extra spaces in Bearer token are handled."""
    call_next = AsyncMock(return_value="success")

    # Test with extra spaces
    mock_request = Mock()
    mock_request.headers = {"authorization": f"Bearer   {valid_auth_token}   "}

    with patch("main.get_http_request", return_value=mock_request):
        result = await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    assert result == "success"
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_middleware_propagates_tool_errors(
    auth_middleware, mock_middleware_context, mock_http_request_with_auth
):
    """Test that ToolErrors from the actual tool are propagated correctly."""
    # Mock call_next to raise a ToolError
    call_next = AsyncMock(side_effect=ToolError("Tool execution failed"))

    with patch("main.get_http_request", return_value=mock_http_request_with_auth):
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify it's the original error
    assert "Tool execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_middleware_wraps_unexpected_exceptions(
    auth_middleware, mock_middleware_context, mock_http_request_with_auth
):
    """Test that unexpected exceptions are caught and wrapped in ToolError."""
    # Mock call_next to raise an unexpected exception
    call_next = AsyncMock(side_effect=ValueError("Unexpected error"))

    # Mock the validator to avoid the early exit
    with patch("main.get_http_request", return_value=mock_http_request_with_auth):
        # This should succeed authentication but fail on call_next
        # The middleware wraps unexpected exceptions in ToolError
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify the error message contains the original error
    assert "Unexpected error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_middleware_initialization(auth_middleware):
    """Test that middleware initializes correctly with validator."""
    assert auth_middleware.validator is not None
    assert hasattr(auth_middleware.validator, "validate_token")


@pytest.mark.asyncio
async def test_middleware_empty_bearer_token(auth_middleware, mock_middleware_context):
    """Test that empty Bearer token is rejected."""
    call_next = AsyncMock()

    # Create request with empty token
    mock_request = Mock()
    mock_request.headers = {"authorization": "Bearer "}

    with patch("main.get_http_request", return_value=mock_request):
        with pytest.raises(ToolError) as exc_info:
            await auth_middleware.on_call_tool(mock_middleware_context, call_next)

    # Verify error (empty token should fail validation)
    assert "Authentication failed" in str(exc_info.value) or "Invalid" in str(
        exc_info.value
    )
    call_next.assert_not_awaited()
