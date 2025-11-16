#!/usr/bin/env python3
"""
Authenticated HTTP Client Example for MCP Joke Server

This example demonstrates how to connect to the MCP server using HTTP transport
with Bearer token authentication.

Requirements:
- Server must be running with HTTP transport (MCP_PROTOCOL=http)
- LOCAL_TOKEN must be set in server's environment
- httpx package must be installed

Usage:
    python examples/authenticated_http_client.py
"""

import asyncio
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server configuration
SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
LOCAL_TOKEN = os.getenv("LOCAL_TOKEN")

if not LOCAL_TOKEN:
    raise ValueError(
        "LOCAL_TOKEN environment variable is required. "
        "Please set it in your .env file or export it."
    )


class AuthenticatedMCPClient:
    """HTTP client for MCP server with Bearer token authentication."""

    def __init__(self, base_url: str, token: str):
        """
        Initialize the authenticated MCP client.

        Args:
            base_url: Base URL of the MCP server
            token: Bearer token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] | None = None) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Optional arguments for the tool

        Returns:
            Tool result

        Raises:
            httpx.HTTPError: If the request fails
        """
        payload = {
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }

        print(f"📤 Calling tool: {tool_name}")
        print(f"   Arguments: {arguments or '{}'}")

        response = await self.client.post(f"{self.base_url}/call-tool", json=payload)
        response.raise_for_status()

        result = response.json()
        print(f"✅ Success: {result}\n")
        return result

    async def list_tools(self) -> list:
        """
        List all available tools from the MCP server.

        Returns:
            List of available tools
        """
        print("📋 Fetching available tools...")

        response = await self.client.get(f"{self.base_url}/tools")
        response.raise_for_status()

        tools = response.json()
        print(f"✅ Found {len(tools)} tools\n")
        return tools

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def main():
    """Main function demonstrating authenticated MCP client usage."""
    print("=" * 70)
    print("MCP Joke Server - Authenticated HTTP Client Example")
    print("=" * 70)
    print()

    async with AuthenticatedMCPClient(SERVER_URL, LOCAL_TOKEN) as client:
        try:
            # List available tools
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.get('name', 'Unknown')}")
            print()

            # Call various tools
            print("-" * 70)
            print("Testing Joke Tools")
            print("-" * 70)
            print()

            # 1. Get consistent joke
            await client.call_tool("tool_get_consistent_joke")

            # 2. Get random joke
            await client.call_tool("tool_get_joke")

            # 3. Get joke by ID
            await client.call_tool("tool_get_joke_by_id", {"joke_id": 42})

            # 4. Get joke by type
            await client.call_tool("tool_get_joke_by_type", {"joke_type": "programming"})

            # 5. Test async variant
            await client.call_tool("tool_aget_joke")

            print("=" * 70)
            print("✨ All tests completed successfully!")
            print("=" * 70)

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            if e.response.status_code == 401:
                print("\n💡 Tip: Check that your LOCAL_TOKEN matches the server's token")
        except httpx.RequestError as e:
            print(f"❌ Request Error: {e}")
            print("\n💡 Tip: Make sure the server is running on", SERVER_URL)
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")


def test_without_auth():
    """
    Demonstrate what happens when authentication fails.

    This function shows the error response when no token or invalid token is provided.
    """
    print("\n" + "=" * 70)
    print("Testing Authentication Failure")
    print("=" * 70)
    print()

    async def _test():
        # Create client with invalid token
        async with httpx.AsyncClient() as client:
            try:
                # Request without authentication
                print("📤 Attempting request without authentication...")
                response = await client.post(
                    f"{SERVER_URL}/call-tool",
                    json={"method": "tools/call", "params": {"name": "tool_get_joke"}},
                )
                response.raise_for_status()
                print("⚠️  Unexpected: Request succeeded without auth!")
            except httpx.HTTPStatusError as e:
                print(f"✅ Expected failure: {e.response.status_code}")
                print(f"   Error message: {e.response.text}")

            try:
                # Request with invalid token
                print("\n📤 Attempting request with invalid token...")
                response = await client.post(
                    f"{SERVER_URL}/call-tool",
                    headers={"Authorization": "Bearer invalid-token-123"},
                    json={"method": "tools/call", "params": {"name": "tool_get_joke"}},
                )
                response.raise_for_status()
                print("⚠️  Unexpected: Request succeeded with invalid token!")
            except httpx.HTTPStatusError as e:
                print(f"✅ Expected failure: {e.response.status_code}")
                print(f"   Error message: {e.response.text}")

    asyncio.run(_test())
    print()


if __name__ == "__main__":
    # Run main authenticated examples
    asyncio.run(main())

    # Optionally test authentication failures
    # Uncomment the line below to see what happens without proper authentication
    # test_without_auth()
