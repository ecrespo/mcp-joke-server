# mcp-joke-server

Simple Model Context Protocol (MCP) tools server that exposes a handful of joke-related tools. It fetches jokes from an external HTTP API and provides them to MCP-compatible clients via the FastMCP framework.

## Overview

This repository implements an MCP server using `fastmcp`. The server defines four tools:

- `tool_get_consistent_joke()` — returns the same hardcoded joke every time.
- `tool_get_joke()` — fetches a random joke from an external jokes API.
- `tool_get_joke_by_id(joke_id)` — fetches a joke by numeric ID.
- `tool_get_joke_by_type(joke_type)` — fetches a joke by category (`general`, `knock-knock`, `programming`, `dad`).

The external API base URL is configured via the `API_BASE_URL` environment variable (see Environment Variables).

## Stack

- Language: Python (requires Python 3.13+ per `pyproject.toml`)
- Framework: [fastmcp]
- HTTP client: `httpx`
- Data validation: `pydantic` (type hints) and `dataclasses`
- Logging/UX: `loguru` and `rich`
- Config: `python-decouple` (loads environment from `.env`)
- Package manager: `uv` (detected via `uv.lock`). Pip also works if you prefer.

## Requirements

- Python 3.13 or newer
- `uv` (recommended) or `pip`
- Network access to the configured jokes API (`API_BASE_URL`)

## Project Structure

```
.
├── LICENSE
├── README.md
├── main.py                    # MCP server entry point (starts FastMCP)
├── pyproject.toml             # Project metadata and dependencies
├── uv.lock                    # uv lockfile (indicates uv is used)
├── utils/
│   ├── RequestAPIJokes.py     # HTTP requests to the jokes API
│   ├── Utils.py               # helpers (e.g., extract_joke)
│   ├── __init__.py
│   ├── config.py              # environment/config handling (python-decouple)
│   ├── constants.py           # constants (API base URL, joke types, sample joke)
│   ├── logger.py              # rich/loguru logger setup and helpers
│   └── model.py               # dataclasses for Joke/Jokes
└── logs/
    ├── mcp_server.log         # runtime log (default)
    └── errors.log             # optional error logs
```

## Environment Variables

Configuration is loaded using `python-decouple`. Create a `.env` file in the project root or export variables in your shell.

Required:

- `API_BASE_URL` — Base URL of the jokes API.
  - TODO: Document the canonical API used in this project (example: https://official-joke-api.appspot.com). Verify endpoints used by `utils/RequestAPIJokes.py`:
    - `/random_joke`
    - `/random_ten`
    - `/jokes/{id}`
    - `/jokes/{type}/random`

Optional (defaults shown in `utils/config.py`):

- `MCP_SERVER_HOST` (default: `0.0.0.0`) — Not currently used by `fastmcp` stdio mode; kept for future use.
- `MCP_SERVER_PORT` (default: `8000`) — Not currently used by `fastmcp` stdio mode; kept for future use.
- `LOG_LEVEL` (default: `INFO`)
- `LOG_FILE` (default: `logs/mcp_server.log`)
- `LOG_ROTATION` (default: `10 MB`)
- `LOG_RETENTION` (default: `7 days`)
- `SESSION_TIMEOUT` (default: `3600`)
- `SESSION_CLEANUP_INTERVAL` (default: `300`)

Example `.env`:

```
API_BASE_URL=https://official-joke-api.appspot.com
LOG_LEVEL=INFO
```

## Setup

Using uv (recommended):

```
uv sync
```

Or with pip:

```
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

## Run

The server entry point is `main.py` which starts FastMCP via `mcp.run()`.

Using uv:

```
uv run python main.py
```

Using pip/venv:

```
python main.py
```

Notes:

- `fastmcp` typically serves MCP over stdio for MCP-compatible clients. If you intend to connect from an MCP client (e.g., editors or AI assistants that support MCP), configure the client to launch this repository via the run command above. TODO: Add a concrete example and client configuration snippet for a specific MCP client.

## Available Tools (MCP)

Defined in `main.py`:

- `tool_get_consistent_joke() -> str`
- `tool_get_joke() -> str`
- `tool_get_joke_by_id(joke_id: int) -> str` (valid range 1–451 per type hints)
- `tool_get_joke_by_type(joke_type: Literal["general", "knock-knock", "programming", "dad"]) -> str`

Tool behavior is implemented via `utils/RequestAPIJokes.py` and helpers in `utils/Utils.py`.

## Scripts

No custom `pyproject.toml` scripts are defined. Use the following commands directly:

- Install dependencies: `uv sync` or `pip install -e .`
- Run server: `uv run python main.py` or `python main.py`

## Tests

There are currently no automated tests in this repository.

TODOs:

- Add unit tests for `utils/RequestAPIJokes.py` (mock HTTP with `respx` or `pytest-httpx`).
- Add tests for `main.py` MCP tools (unit tests around tool functions; consider separating logic from IO).

## Troubleshooting

- If you see errors fetching jokes, verify `API_BASE_URL` is set correctly and reachable.
- Logs are written to `logs/mcp_server.log` by default. Adjust via `LOG_FILE` and `LOG_LEVEL` in your environment.

## License

This project is licensed under the GNU General Public License v3.0 — see the `LICENSE` file for details.

## Acknowledgements

- [FastMCP](https://pypi.org/project/fastmcp/) for the MCP server framework.
- The external jokes API (document exact source as a TODO once confirmed).