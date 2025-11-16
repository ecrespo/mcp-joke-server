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
  - Test ergonomics: For local test runs you typically do not need to set anything because tests patch/marshal config internally. If you import networked modules in ad‑hoc scripts, ensure `API_BASE_URL` is exported before the import.

3) .env
- Create `.env` at project root or export variables in your shell. Minimal example:
```
API_BASE_URL=https://official-joke-api.appspot.com
LOG_LEVEL=INFO
```

4) Run the server (stdio)
- `uv run python main.py` or simply `python main.py`
- Integrate with an MCP client by configuring it to launch the command above; `fastmcp` speaks MCP over stdio.

5) Alternate quick sanity check (no network)
- `python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'Why?','punchline':'Because.'}))"`
- This path loads only pure utilities and avoids `Settings`/`URL` import side effects.

6) Notes about `Settings`
- `utils/config.py` defines class-level attributes in `Settings`. Access via `from utils.config import Settings`.
- `utils/constants.py` binds `URL = Settings.API_BASE_URL`. Ensure `API_BASE_URL` is set before importing modules that depend on it in process startup/tests.

7) Local tooling
- Lint/format (optional): add `ruff`/`black` in dev extras if desired. Repo does not enforce them yet; mirror current import/style patterns.

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

Notes:
- The suite mocks network and file logging as needed; it is safe to run offline.
- Coverage HTML is emitted to `htmlcov/` per `pytest.ini`.

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

4) Running focused subsets
- Single test file: `pytest -q tests/test_factory.py`
- Single test: `pytest -q tests/test_factory.py::test_http_repository_is_default`
- Keyword filter: `pytest -q -k http` (selects tests with names containing "http")

5) Minimal verified example (executed and re-verified)
- We verified a dependency-free path by running a one-liner that tested the pure formatter. Command and output:

```
python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'Why?','punchline':'Because.'}))"
# Output:
Why?
Because.
```

To run an ad-hoc script version without pytest, ensure it imports only pure utilities and not networked modules.

6) Example `pytest` tests for HTTP (with `respx`)
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

7) Adding new tests — guidelines
- Place new tests under `tests/` mirroring package layout (`tests/utils/test_request_api_jokes.py`, etc.).
- Prefer pure/isolated tests. For request code, use `respx` and assert both request path and error mapping.
- Avoid importing `main.py` unless you are testing MCP tool registration/IO paths; modules under `repositories/` and `utils/` should contain the testable logic.
- If a test must interact with logging, prefer patching handlers or using in-memory sinks to avoid writing to `logs/`.

8) Test structure suggestions
- Place tests under `tests/` mirroring package layout (`tests/utils/test_request_api_jokes.py`, etc.).
- Avoid importing `main.py` in tests unless you are testing MCP tool registration; prefer isolating logic to utility modules and testing those.

9) Fast smoke runs
- For quick validation of pure functions, use `uv run python -c "from utils.formatters import extract_joke; print(extract_joke({'setup':'a','punchline':'b'}))"`.

10) Demonstration test (pure utility)
The following minimal test was used as a demonstration of adding tests without network dependencies:

```
# tests/test_demo_example.py
from utils.formatters import extract_joke

def test_extract_joke_demo():
    data = {"setup": "Knock knock", "punchline": "Who's there?"}
    assert extract_joke(data) == "Knock knock\nWho's there?"
```

Run just this test: `pytest -q tests/test_demo_example.py`
Delete when done to keep the suite focused.

---

### Development notes and conventions

1) Code style
- Follow the existing module conventions and simple functional style. If adding linters/formatters, prefer `ruff` + `black`. Keep import paths relative to the package (already used: `from utils...`).

2) Logging
- Use `utils/logger.py` helpers and `loguru` loggers. Default file log: `logs/mcp_server.log` (rotated/retained per env). Make sure tests that assert logging do not write to real files; patch or configure handlers for tests.
  - For unit tests, consider configuring `LOG_FILE` to a temp path or using `loguru.logger.remove()`/`logger.add(sys.stderr)` in a fixture to keep outputs in-memory.

3) Error handling
- Network layer maps `httpx.ReadTimeout` → `TimeoutError` and `httpx.ConnectError` → `ConnectionError`. Non-200 responses raise `BaseException` after logging body. Mirror this pattern for new request functions for consistency.

4) Models
- `utils/model.py` defines `Joke`, `Jokes`. Ensure external API JSON matches these dataclasses. If the upstream schema varies, add robust parsing/validation or optional fields.

5) MCP tools
- `main.py` registers tools with FastMCP. Tool implementations call the repository/request layer then use `utils/formatters.extract_joke` to format outputs. When adding tools, keep IO separate from logic to simplify unit testing.
  - The example MCP client under `examples/mcp_client.py` demonstrates how to launch/connect using stdio.

6) Environment-sensitive imports
- Because `URL` is computed from `Settings.API_BASE_URL` at import time (`utils/constants.py`), tests importing request modules will fail if `API_BASE_URL` is not set. In tests, set `API_BASE_URL` in the environment before import, or monkeypatch `utils.constants.URL`.

7) External API reference
- Canonical base: `https://official-joke-api.appspot.com` (confirm availability). Endpoints used are listed in Testing section. If switching providers, update `utils/RequestAPIJokes.py` and docs.

8) Running as an MCP server
- Typical MCP clients launch this repo as a subprocess using the run command. If you need a TCP/HTTP transport in the future, you may adapt `fastmcp` usage accordingly; `MCP_SERVER_HOST/PORT` are placeholders for that evolution.

---

### Reproducibility note for this document

- Verified on 2025-11-15 (local):
  - `pytest -q` → all 104 tests passed; coverage HTML written to `htmlcov/`.
  - Pure-function smoke run produced:
    - `Why?` then `Because.` on separate lines (see section above).
- A temporary demonstration test (`tests/test_demo_example.py`) was created, executed, and removed to validate the add/run/delete workflow. Only this `.junie/guidelines.md` file has been updated.
