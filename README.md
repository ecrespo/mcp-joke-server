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
MCP_PROTOCOL=stdio
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

TODO: The Compose file includes a healthcheck referencing `/health`; confirm or implement a matching endpoint in HTTP mode.

## Design Notes

- Repository Pattern (`repositories/*`) abstracts data access and enables caching.
- Strategy Pattern (`strategies/*`) selects transport and validates configuration.
- Utilities under `utils/` include a typed HTTP client, models, logging, and formatters.

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