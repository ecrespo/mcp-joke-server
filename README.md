# mcp-joke-server

MCP tools server that exposes joke-related tools. It fetches jokes from an external HTTP API and serves them to MCP-compatible clients via FastMCP. Multiple transports are supported by a Strategy pattern: stdio (default), HTTP, and SSE.

## Overview

This repository implements an MCP server using `fastmcp` with a clean separation of concerns:

- Tools in `main.py` expose joke operations to MCP clients.
- A Repository layer under `repositories/` fetches and caches jokes.
- Transport strategies under `strategies/` select stdio/HTTP/SSE at runtime.
- Utilities under `utils/` provide HTTP clients, models, formatting, and logging.

Exposed tools (sync):

- `tool_get_consistent_joke()` — returns the same hardcoded joke every time.
- `tool_get_joke()` — fetches a random joke from the external API.
- `tool_get_joke_by_id(joke_id)` — fetches a joke by numeric ID.
- `tool_get_joke_by_type(joke_type)` — fetches a joke by category (`general`, `knock-knock`, `programming`, `dad`).

Async variants are also available: `tool_aget_joke`, `tool_aget_joke_by_id`, `tool_aget_joke_by_type`.

The jokes API base URL is configured via `API_BASE_URL`. Transport is selected by `MCP_PROTOCOL` (`stdio`, `http`, `sse`).

## Stack

- Language: Python 3.13+
- Framework: `fastmcp` (MCP over stdio/HTTP/SSE)
- HTTP client: `httpx`
- Config/validation: `pydantic`, `pydantic-settings`
- Env loader: `python-dotenv` (via `pydantic-settings`)
- Logging/UX: `loguru`, `rich`
- Package manager: `uv` (lockfile `uv.lock` present). `pip` also works.
- Entry point: `main.py`

## Requirements

- Python 3.13+
- `uv` (recommended) or `pip`
- Network access to the configured jokes API (`API_BASE_URL`)

## Project Structure

```
.
├── LICENSE
├── README.md
├── main.py                     # MCP server entry point (starts FastMCP)
├── pyproject.toml              # Project metadata and dependencies
├── uv.lock                     # uv lockfile
├── repositories/               # Repository pattern (HTTP + cached repositories)
│   ├── base.py
│   ├── cached_repository.py
│   ├── factory.py
│   ├── http_repository.py
│   └── __init__.py
├── strategies/                 # Strategy pattern for transports (stdio/http/sse)
│   ├── base.py
│   ├── factory.py
│   ├── http_strategy.py
│   ├── sse_strategy.py
│   ├── stdio_strategy.py
│   └── __init__.py
├── utils/
│   ├── RequestAPIJokes.py      # HTTP/async client for the jokes API
│   ├── config.py               # Settings via pydantic-settings
│   ├── constants.py            # URL, joke types, consistent joke
│   ├── exceptions.py
│   ├── formatters.py           # pure helpers (e.g., extract_joke)
│   ├── logger.py
│   ├── logging_config.py
│   ├── logging_interfaces.py
│   ├── rich_renderers.py
│   └── model.py                # dataclasses for Joke/Jokes
├── tests/                      # Pytest suite
├── docs/                       # Architecture/testing docs
├── examples/                   # Example MCP client and demos
├── Makefile                    # Developer commands (see Scripts)
├── docker-compose.yml          # HTTP/SSE/stdio services
├── Dockerfile                  # Multi-stage Docker build
└── htmlcov/                    # Coverage HTML (generated)
```

## Environment Variables

Loaded with `pydantic-settings`; `.env` at project root is supported.

Required:

- `API_BASE_URL` — Base URL of the jokes API. Example: `https://official-joke-api.appspot.com`
  - Endpoints used by `utils/RequestAPIJokes.py`:
    - `GET /random_joke`
    - `GET /random_ten`
    - `GET /jokes/{id}`
    - `GET /jokes/{type}/random`

- `LOCAL_TOKEN` — Authentication token for HTTP/SSE transports. Used to secure tool access via Bearer token authentication.
  - Example: `LOCAL_TOKEN=-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys`
  - **Note:** STDIO transport does not require authentication as it runs in a trusted local environment.

Optional (defaults in `utils/config.py`):

- `MCP_PROTOCOL` (default `stdio`) — `stdio`, `http`, or `sse`
- `MCP_SERVER_HOST` (default `0.0.0.0`) — host for HTTP/SSE
- `MCP_SERVER_PORT` (default `8000`) — port for HTTP/SSE
- `LOG_LEVEL` (default `INFO`)
- `LOG_FILE` (default `logs/mcp_server.log`)
- `LOG_ROTATION` (default `10 MB`)
- `LOG_RETENTION` (default `7 days`)
- `SESSION_TIMEOUT` (default `3600`)
- `SESSION_CLEANUP_INTERVAL` (default `300`)

Example `.env`:

```
API_BASE_URL=https://official-joke-api.appspot.com
LOCAL_TOKEN=-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys
MCP_PROTOCOL=http
LOG_LEVEL=INFO
```

Notes:

- `utils/constants.py` binds `URL = Settings.API_BASE_URL` at import time; set `API_BASE_URL` before importing networked modules in ad‑hoc scripts/tests.

## Setup

Using uv (recommended):

```
uv sync
```

Using pip/venv:

```
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

## Run

Entry point: `main.py`. Select transport with `MCP_PROTOCOL`.

- stdio (default):

```
MCP_PROTOCOL=stdio uv run python main.py
```

- HTTP:

```
MCP_PROTOCOL=http uv run python main.py  # uses Settings.MCP_SERVER_HOST/PORT
```

- SSE:

```
MCP_PROTOCOL=sse uv run python main.py   # uses Settings.MCP_SERVER_HOST/PORT
```

Using pip/venv, replace `uv run` with `python` as needed.

Tip: For stdio, configure your MCP client to launch the command above as a subprocess.

## Claude Desktop Configuration

Claude Desktop can connect to this MCP server using the stdio transport. Configure it by editing the Claude Desktop configuration file.

### Configuration File Location

The configuration file location depends on your operating system:

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

If the file doesn't exist, create it with the appropriate content below.

### Configuration with uv (Recommended)

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "joke-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-joke-server",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "API_BASE_URL": "https://official-joke-api.appspot.com",
        "LOCAL_TOKEN": "your-secret-token-here",
        "MCP_PROTOCOL": "stdio",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/mcp-joke-server` with the actual absolute path to your project directory.

### Configuration with Python Virtual Environment

If using a virtual environment instead of uv:

```json
{
  "mcpServers": {
    "joke-server": {
      "command": "/absolute/path/to/mcp-joke-server/.venv/bin/python",
      "args": [
        "main.py"
      ],
      "cwd": "/absolute/path/to/mcp-joke-server",
      "env": {
        "API_BASE_URL": "https://official-joke-api.appspot.com",
        "LOCAL_TOKEN": "your-secret-token-here",
        "MCP_PROTOCOL": "stdio",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "joke-server": {
      "command": "C:\\Users\\YourName\\Projects\\mcp-joke-server\\.venv\\Scripts\\python.exe",
      "args": [
        "main.py"
      ],
      "cwd": "C:\\Users\\YourName\\Projects\\mcp-joke-server",
      "env": {
        "API_BASE_URL": "https://official-joke-api.appspot.com",
        "LOCAL_TOKEN": "your-secret-token-here",
        "MCP_PROTOCOL": "stdio",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Environment Variables

Required:
- `API_BASE_URL`: URL of the jokes API
- `LOCAL_TOKEN`: Authentication token (required for server initialization, but not validated in stdio mode)

Optional:
- `MCP_PROTOCOL`: Set to `stdio` for Claude Desktop (default)
- `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `LOG_FILE`: Path to log file (default: `logs/mcp_server.log`)

### Verifying the Configuration

After configuring Claude Desktop:

1. **Restart Claude Desktop** completely (quit and reopen)
2. **Check the server status:**
   - Open Claude Desktop
   - Look for the MCP icon (usually in the toolbar or settings)
   - Verify "joke-server" appears in the list of available servers
   - Check if it shows as "Connected" or "Running"

3. **Test the connection:**
   - Ask Claude to use the joke tools
   - Example prompt: "Can you get me a random joke using the available tools?"
   - Claude should be able to call `tool_get_joke` and other registered tools

### Troubleshooting Claude Desktop Connection

**Server doesn't appear in Claude Desktop:**
- Check the JSON syntax in `claude_desktop_config.json` (use a JSON validator)
- Verify the file is saved in the correct location for your OS
- Ensure the file has the correct name: `claude_desktop_config.json`
- Restart Claude Desktop after making changes

**Server appears but shows as "Failed" or "Error":**
- Check that the paths are absolute (not relative)
- Verify the Python executable or uv command exists at the specified path
- Ensure all environment variables are set correctly
- Check the Claude Desktop logs for detailed error messages

**Claude Desktop Logs Location:**

- **macOS:** `~/Library/Logs/Claude/mcp*.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp*.log`
- **Linux:** `~/.config/Claude/logs/mcp*.log`

**Tools work but return errors:**
- Verify `API_BASE_URL` is accessible from your network
- Check that `LOCAL_TOKEN` is set (even though stdio doesn't validate it, the server requires it)
- Review the server logs in `logs/mcp_server.log` for detailed error information

**Permission Issues (macOS/Linux):**
```bash
# Make sure the Python executable is executable
chmod +x /path/to/.venv/bin/python

# Ensure the project directory is readable
chmod -R 755 /path/to/mcp-joke-server
```

### Using Multiple MCP Servers

You can configure multiple MCP servers in Claude Desktop:

```json
{
  "mcpServers": {
    "joke-server": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-joke-server", "run", "python", "main.py"],
      "env": {
        "API_BASE_URL": "https://official-joke-api.appspot.com",
        "LOCAL_TOKEN": "token-1",
        "MCP_PROTOCOL": "stdio"
      }
    },
    "another-server": {
      "command": "/path/to/another-server",
      "args": ["--config", "config.json"],
      "env": {
        "SOME_VAR": "value"
      }
    }
  }
}
```

### Development Tips

**Viewing Server Output:**

Since Claude Desktop runs the server as a background process, you won't see stdout directly. Check the logs:

```bash
# Monitor server logs in real-time
tail -f logs/mcp_server.log
```

**Testing Configuration Before Adding to Claude Desktop:**

Test your configuration manually first:

```bash
# Run the exact command Claude Desktop will use
uv --directory /absolute/path/to/mcp-joke-server run python main.py

# Or with venv
/absolute/path/to/.venv/bin/python main.py
```

If this command works, the Claude Desktop configuration should work too.

**Hot Reloading:**

When you make code changes:
1. Claude Desktop must be restarted to reload the server
2. Or disconnect and reconnect the server from Claude Desktop settings
3. The server process is killed and restarted each time

## Scripts (Makefile)

Developer-friendly commands are provided in the `Makefile`:

- `make install` → `uv sync`
- `make install-dev` → `uv sync --extra dev`
- `make test` → run pytest with coverage (HTML/XML/term)
- `make test-quick` → run pytest, stop on first failure
- `make lint` / `make lint-fix` → Ruff checks (and autofix)
- `make format` / `make format-check` → Ruff format + Black
- `make type-check` → mypy
- `make ci-local` → lint, format-check, type-check, test
- Docker helpers: `docker-build`, `docker-up`, `docker-up-sse`, `docker-up-stdio`, `docker-up-detached`, `docker-down`, `docker-logs`, `docker-clean`
- Run locally: `make run` (stdio), or `run-http` / `run-sse` / `run-stdio`

## Tests

Pytest is used with coverage reporting (`pytest.ini`). The suite mocks network and file logging as needed; safe to run offline.

With uv:

```
uv sync --extra dev
uv run -m pytest -q
```

With pip/venv:

```
pip install -e .[dev]
pytest -q
```

Focused subsets:

- Single file: `pytest -q tests/test_factory.py`
- Single test: `pytest -q tests/test_factory.py::test_http_repository_is_default`
- Keyword: `pytest -q -k http`

Quick pure-function smoke (no network):

```
python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'Why?','punchline':'Because.'}))"
```

Coverage HTML is written to `htmlcov/`.

## Docker

Multi-stage Dockerfile and Compose are provided.

Quick start:

```
docker compose up mcp-server-http          # HTTP transport on :8000
docker compose --profile sse up mcp-server-sse  # SSE transport on :8001
docker compose --profile stdio up mcp-server-stdio  # stdio (dev)
```

See `DOCKER.md` for more details.

## Authentication

The server implements Bearer token authentication for HTTP and SSE transports via a custom middleware (`LocalTokenAuthMiddleware` in `main.py`).

### How it Works

- **HTTP/SSE Transports**: All tool calls require a valid Bearer token in the `Authorization` header
- **STDIO Transport**: No authentication required (runs in trusted local environment)

### Usage

Include the token in your HTTP requests:

```bash
# Example: Call a tool with authentication
curl -X POST http://localhost:8000/call-tool \
  -H "Authorization: Bearer -KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys" \
  -H "Content-Type: application/json" \
  -d '{"name": "tool_get_joke"}'
```

For a complete Python client example with authentication, see `examples/authenticated_http_client.py`.

### Token Validation

The `LocalTokenValidator` class (`utils/auth.py`) validates tokens by comparing them with the `LOCAL_TOKEN` environment variable. Failed authentication returns a `ToolError` with a descriptive message.

### Security Notes

- Always use HTTPS in production to protect tokens in transit
- Rotate tokens periodically
- Never commit tokens to version control
- Use environment variables or secrets management systems

## Testing with MCP Inspector

The MCP Inspector allows you to explore and invoke server tools interactively. It supports both stdio and HTTP transports and requires Node.js 18+ to use `npx`.

### Installation

The Inspector doesn't require permanent installation:

```bash
npx @modelcontextprotocol/inspector@latest --help
```

### Option A: stdio Transport (No Authentication Required)

The Inspector launches the server as a subprocess. Environment variables must be passed with `--env`.

With uv:

```bash
npx @modelcontextprotocol/inspector@latest \
  --command "uv run python main.py" \
  --env API_BASE_URL=https://official-joke-api.appspot.com \
  --env LOCAL_TOKEN=your-secret-token-here \
  --env MCP_PROTOCOL=stdio
```

With pip/venv:

```bash
npx @modelcontextprotocol/inspector@latest \
  --command "python main.py" \
  --env API_BASE_URL=https://official-joke-api.appspot.com \
  --env LOCAL_TOKEN=your-secret-token-here \
  --env MCP_PROTOCOL=stdio
```

**Note:** Although `LOCAL_TOKEN` is required for the server to start, stdio transport does not enforce authentication as it runs in a trusted local environment.

### Option B: HTTP Transport (Authentication Required)

For HTTP transport, you need two terminals: one to run the server and another to connect the Inspector.

#### Terminal 1: Start the HTTP Server

```bash
API_BASE_URL=https://official-joke-api.appspot.com \
LOCAL_TOKEN=-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys \
MCP_PROTOCOL=http \
MCP_SERVER_HOST=127.0.0.1 \
MCP_SERVER_PORT=8000 \
uv run python main.py
```

Or with pip/venv:

```bash
API_BASE_URL=https://official-joke-api.appspot.com \
LOCAL_TOKEN=-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys \
MCP_PROTOCOL=http \
MCP_SERVER_HOST=127.0.0.1 \
MCP_SERVER_PORT=8000 \
python main.py
```

#### Terminal 2: Connect Inspector with Authentication

The Inspector needs to send the Bearer token with every request:

```bash
# Using environment variable for token
export LOCAL_TOKEN="-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys"

npx @modelcontextprotocol/inspector@latest \
  --server-url http://127.0.0.1:8000 \
  --header "Authorization: Bearer $LOCAL_TOKEN"
```

Or directly inline:

```bash
npx @modelcontextprotocol/inspector@latest \
  --server-url http://127.0.0.1:8000 \
  --header "Authorization: Bearer -KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys"
```

**Important:** The Inspector must include the `Authorization` header with a valid Bearer token, or all tool calls will fail with authentication errors.

### What to Test

Once connected, you should see the registered tools. Try these quick tests:

- **No network required:** `tool_get_consistent_joke`
- **Random joke:** `tool_get_joke`
- **By ID:** `tool_get_joke_by_id` with `joke_id=42`
- **By type:** `tool_get_joke_by_type` with `joke_type="programming"`
- **Async variants:** `tool_aget_joke`, `tool_aget_joke_by_id`, etc.

### Troubleshooting Inspector Connection

**Authentication Errors (HTTP/SSE only):**
- Verify the `Authorization` header is included with `--header`
- Check that the token matches the server's `LOCAL_TOKEN`
- Ensure the token format is: `Bearer <token>`

**Connection Timeouts:**
- Verify `API_BASE_URL` is set and accessible
- Ensure the server is running and listening on the correct host/port
- For HTTP, confirm the Inspector URL matches the server's host/port

**Command Not Found:**
- The `--command` must be exactly how you start the server
- Include the full path if using a virtual environment

## Design Notes

- **Middleware Pattern** (`main.py`): `LocalTokenAuthMiddleware` intercepts tool calls to enforce authentication for HTTP/SSE transports
- **Repository Pattern** (`repositories/*`): Abstracts data access and enables caching
- **Strategy Pattern** (`strategies/*`): Selects transport and validates configuration
- **Utilities** (`utils/`): Include typed HTTP client, models, logging, formatters, and authentication

Further docs: see `docs/` (architecture diagrams, testing notes, refactoring summaries).

## License

GPL-3.0 — see `LICENSE`.

## TODOs

- Verify and align package version (`pyproject.toml` currently `0.1.0`) with `docs/CHANGELOG.md`.
- CI: No workflow files were found in this repo listing; if CI is desired, add a workflow and document it here.

## Troubleshooting

- If fetching jokes fails, verify `API_BASE_URL` and network access.
- Logs default to `logs/mcp_server.log`; adjust via env vars (`LOG_*`).
- In ad‑hoc scripts/tests, ensure `API_BASE_URL` is set before importing networked modules.

## Acknowledgements

- [FastMCP](https://pypi.org/project/fastmcp/) for the MCP server framework.
- Jokes API: https://official-joke-api.appspot.com (public example provider).