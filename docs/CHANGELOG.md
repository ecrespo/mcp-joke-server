# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.3.0] - 2025-11-16

### Added
- Docker workflow and compose profiles added; initial CI/CD pipeline configuration to streamline builds and local runs. ([85db8e8](https://github.com/ecrespo/mcp-joke-server/commit/85db8e8))

### Changed
- Switched environment management from `python-decouple` to `python-dotenv` for simpler local development and `.env` handling. ([1675032](https://github.com/ecrespo/mcp-joke-server/commit/1675032))
- README/docs refinements: expanded usage instructions, logging information, Inspector integration guidance, and general clarity improvements. ([6ede69d](https://github.com/ecrespo/mcp-joke-server/commit/6ede69d), [9e1ec83](https://github.com/ecrespo/mcp-joke-server/commit/9e1ec83))
- Test suite expanded with comprehensive async and integration coverage (no runtime behavior changes). ([39f5c63](https://github.com/ecrespo/mcp-joke-server/commit/39f5c63))

### Deprecated
- None.

### Removed
- None.

### Fixed
- None.

### Security
- None.

## [0.2.2] - 2025-11-15

### Added
- Architecture documentation with detailed diagrams and C4 model. ([b2c4cf2](https://github.com/ecrespo/mcp-joke-server/commit/b2c4cf2))
- README expanded with SSE transport support, async tool variants, and updated testing/documentation sections. ([9d4b563](https://github.com/ecrespo/mcp-joke-server/commit/9d4b563))
- Implemented Strategy Pattern for MCP transport protocols. ([66be054](https://github.com/ecrespo/mcp-joke-server/commit/66be054))

### Changed
- Refactored logging across strategies, repositories, and API clients to support dependency injection. ([ff40c9a](https://github.com/ecrespo/mcp-joke-server/commit/ff40c9a))
- Refactored MCP server initialization to follow dependency injection principles. ([b831451](https://github.com/ecrespo/mcp-joke-server/commit/b831451))

### Deprecated
- None.

### Removed
- None.

### Fixed
- None.

### Security
- None.

## [0.2.1] - 2025-11-15

### Added
- Modular logging components introduced:
  - Dedicated configuration module `utils/logging_config.py` and rich-based console renderer `utils/rich_renderers.py` (supports customization). ([5b8b51f](https://github.com/ecrespo/mcp-joke-server/commit/5b8b51f))
  - Reusable interfaces/protocols in `utils/logging_interfaces.py` for dependency injection. ([5b8b51f](https://github.com/ecrespo/mcp-joke-server/commit/5b8b51f))

### Changed
- Refactored `utils/logger.py` to delegate configuration and rendering to new modules, improving separation of concerns and maintainability. ([5b8b51f](https://github.com/ecrespo/mcp-joke-server/commit/5b8b51f))
- Replaced `print` statements with structured logging (`loguru`) across examples and repository modules for clearer diagnostics. ([e4895cf](https://github.com/ecrespo/mcp-joke-server/commit/e4895cf))
- Simplified `add_to_tree` in `utils/rich_renderers.py` by extracting helper functions for mappings and sequences; reduced complexity while preserving behavior. ([8901d2f](https://github.com/ecrespo/mcp-joke-server/commit/8901d2f))
- Expanded project documentation (README and developer guidelines) with updated modules, testing strategies, and troubleshooting tips. ([6c850c1](https://github.com/ecrespo/mcp-joke-server/commit/6c850c1))
- Added comprehensive docstrings to `examples/mcp_client.py` to improve clarity and usability. ([a7ae049](https://github.com/ecrespo/mcp-joke-server/commit/a7ae049))

### Deprecated
- None.

### Removed
- None.

### Fixed
- None.

### Security
- None.

## [0.2.0] - 2025-11-15

### Added
- Introduced repository pattern for data access abstraction with new `repositories` module: base interfaces, HTTP and cached implementations, and a factory for creation (7d80866).

### Changed
- Configuration system refactored to use `pydantic-settings` with a Singleton settings pattern; added validators and defaults, and updated dependencies/lockfiles (980d42c).
- `main.py` now integrates the repository pattern (`get_random_joke`, `get_joke_by_id`, `get_jokes_by_type`), improving maintainability and testability; refined response parsing in `utils/RequestAPIJokes.py` (99368f3).
- Expanded and updated README with detailed project structure, testing instructions, and dependency information (53e1a28).

### Removed
- Outdated documentation files removed to reflect the new architecture and structure (d9117aa).

### Deprecated
- None.

### Fixed
- None.

### Security
- None.

## [0.1.0] - 2025-11-15

### Added
- Initial commit and project foundation
