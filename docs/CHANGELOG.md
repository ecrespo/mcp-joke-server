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
