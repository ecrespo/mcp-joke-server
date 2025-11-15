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
