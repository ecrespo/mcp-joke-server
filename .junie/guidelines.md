### mcp-joke-server — Developer Guidelines (Project-Specific)

This document captures build/config, testing, and development practices that are specific to this repository. It assumes you are an experienced Python developer and focuses on project idiosyncrasies rather than generic topics.

#### Stack highlights
- Python 3.13+ (enforced via `pyproject.toml`)
- Dependencies: `fastmcp`, `httpx`, `loguru`, `rich`, `python-decouple`, `pydantic`, `pydantic-settings`
- Preferred package manager: `uv` (a `uv.lock` is present). Pip works if you prefer.
- Runtime model: MCP server over stdio using `fastmcp` (entry point `main.py`).

---

### Build and configuration

1) Install deps
- With uv (recommended):
  - `uv sync`
- With pip/venv:
  - `python -m venv .venv`
  - `. .venv/bin/activate` (Windows: `.venv\Scripts\activate`)
  - `pip install -U pip`
  - `pip install -e .`

2) Environment variables (loaded with `pydantic-settings` and `python-decouple`)
- Required:
  - `API_BASE_URL`: Base URL of the jokes API. Typical value: `https://official-joke-api.appspot.com`
- Optional (defaults in `utils/config.py`):
  - `MCP_SERVER_HOST` (default `0.0.0.0`), `MCP_SERVER_PORT` (default `8000`) — kept for potential future non-stdio modes
  - Logging: `LOG_LEVEL` (default `INFO`), `LOG_FILE` (default `logs/mcp_server.log`), `LOG_ROTATION` (default `10 MB`), `LOG_RETENTION` (default `7 days`)
  - Sessions: `SESSION_TIMEOUT` (default `3600`), `SESSION_CLEANUP_INTERVAL` (default `300`)

3) .env
- Create `.env` at project root or export variables in your shell. Minimal example:
```
API_BASE_URL=https://official-joke-api.appspot.com
LOG_LEVEL=INFO
```

4) Run the server (stdio)
- `uv run python main.py` or simply `python main.py`
- Integrate with an MCP client by configuring it to launch the command above; `fastmcp` speaks MCP over stdio.

5) Notes about `Settings`
- `utils/config.py` defines class-level attributes in `Settings`. Access via `from utils.config import Settings`.
- `utils/constants.py` binds `URL = Settings.API_BASE_URL`. Ensure `API_BASE_URL` is set before importing modules that depend on it in process startup/tests.

---

### Testing

This repository uses `pytest` with coverage reporting (`pytest.ini`). Tests are committed under `tests/` and were verified to pass.

1) Test runner
- With uv:
  - `uv sync --extra dev`
  - `uv run -m pytest -q`
- With pip/venv:
  - `pip install -e .[dev]`
  - `pytest -q`

2) HTTP mocking strategy for `httpx`
- Use one of:
  - `respx` (preferred): powerful router-style mocking for `httpx`
  - `pytest-httpx`: lightweight fixture-based approach
- Add via uv/pip for local development: `uv add --dev respx` or `uv add --dev pytest-httpx`

3) Unit test focus areas
- `utils/formatters.extract_joke(json)` is pure and easy to test.
- `utils/RequestAPIJokes.*` require HTTP mocking. Validate:
  - Correct endpoints per function:
    - `get_joke` → `GET {API_BASE_URL}/random_joke`
    - `get_ten_jokes` → `GET {API_BASE_URL}/random_ten`
    - `get_joke_by_id(id)` → `GET {API_BASE_URL}/jokes/{id}`
    - `get_jokes_by_type(type)` → `GET {API_BASE_URL}/jokes/{type}/random`
  - Non-200 handling logs `response.text` and raises `BaseException` (project-specific pattern)
  - `httpx.ReadTimeout` → `TimeoutError`; `httpx.ConnectError` → `ConnectionError`
  - Mapping to dataclasses in `utils/model.py` (see types `Joke`, `Jokes`) — ensure schema compatibility

4) Minimal verified example (executed during preparation of this guide)
- We verified a dependency-free path by running a one-liner that tested the pure formatter. Command and output:

```
python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'Why?','punchline':'Because.'}))"
# Output:
Why?
Because.
```

To run an ad-hoc script version without pytest, ensure it imports only pure utilities and not networked modules.

5) Example `pytest` tests for HTTP (with `respx`)
```
import respx
import httpx
from utils.RequestAPIJokes import get_joke, get_ten_jokes, get_joke_by_id, get_jokes_by_type
from utils.constants import URL

@respx.mock
def test_get_joke_success():
    route = respx.get(f"{URL}/random_joke").mock(return_value=httpx.Response(200, json={
        "id": 1,
        "type": "general",
        "setup": "Setup",
        "punchline": "Punchline",
    }))
    joke = get_joke()
    assert route.called
    assert joke.setup == "Setup" and joke.punchline == "Punchline"

@respx.mock
def test_get_joke_non_200_raises():
    respx.get(f"{URL}/random_joke").mock(return_value=httpx.Response(500, text="boom"))
    try:
        get_joke()
        assert False, "expected exception"
    except BaseException:
        pass
```

Run with uv:
- `uv run -m pytest -q`

6) Test structure suggestions
- Place tests under `tests/` mirroring package layout (`tests/utils/test_request_api_jokes.py`, etc.).
- Avoid importing `main.py` in tests unless you are testing MCP tool registration; prefer isolating logic to utility modules and testing those.

7) Fast smoke runs
- For quick validation of pure functions, use `uv run python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'a','punchline':'b'}))"`.

---

### Development notes and conventions

1) Code style
- Follow the existing module conventions and simple functional style. If adding linters/formatters, prefer `ruff` + `black`. Keep import paths relative to the package (already used: `from utils...`).

2) Logging
- Use `utils/logger.py` helpers and `loguru` loggers. Default file log: `logs/mcp_server.log` (rotated/retained per env). Make sure tests that assert logging do not write to real files; patch or configure handlers for tests.

3) Error handling
- Network layer maps `httpx.ReadTimeout` → `TimeoutError` and `httpx.ConnectError` → `ConnectionError`. Non-200 responses raise `BaseException` after logging body. Mirror this pattern for new request functions for consistency.

4) Models
- `utils/model.py` defines `Joke`, `Jokes`. Ensure external API JSON matches these dataclasses. If the upstream schema varies, add robust parsing/validation or optional fields.

5) MCP tools
- `main.py` registers tools with FastMCP. Tool implementations call the repository/request layer then use `utils/formatters.extract_joke` to format outputs. When adding tools, keep IO separate from logic to simplify unit testing.

6) Environment-sensitive imports
- Because `URL` is computed from `Settings.API_BASE_URL` at import time (`utils/constants.py`), tests importing request modules will fail if `API_BASE_URL` is not set. In tests, set `API_BASE_URL` in the environment before import, or monkeypatch `utils.constants.URL`.

7) External API reference
- Canonical base: `https://official-joke-api.appspot.com` (confirm availability). Endpoints used are listed in Testing section. If switching providers, update `utils/RequestAPIJokes.py` and docs.

8) Running as an MCP server
- Typical MCP clients launch this repo as a subprocess using the run command. If you need a TCP/HTTP transport in the future, you may adapt `fastmcp` usage accordingly; `MCP_SERVER_HOST/PORT` are placeholders for that evolution.

---

### Reproducibility note for this document

- During preparation, the full pytest suite was executed successfully (100 tests passed with coverage), and a minimal `extract_joke` smoke check was run. No temporary files were committed; only this `.junie/guidelines.md` file is part of this change.
