.PHONY: help install install-dev test lint format type-check clean docker-build docker-up docker-down docker-logs ci-local

# Default target
help:
	@echo "Available commands:"
	@echo "  make install          - Install project dependencies"
	@echo "  make install-dev      - Install project + dev dependencies"
	@echo "  make test             - Run tests with coverage"
	@echo "  make lint             - Run Ruff linter"
	@echo "  make format           - Format code with Ruff and Black"
	@echo "  make format-check     - Check code formatting"
	@echo "  make type-check       - Run mypy type checker"
	@echo "  make ci-local         - Run all CI checks locally"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-up        - Start Docker services"
	@echo "  make docker-down      - Stop Docker services"
	@echo "  make docker-logs      - View Docker logs"
	@echo "  make clean            - Remove build artifacts and cache"

# Installation
install:
	uv sync

install-dev:
	uv sync --extra dev

# Testing
test:
	uv run pytest -v --cov=. --cov-report=xml --cov-report=html --cov-report=term

test-quick:
	uv run pytest -v -x

# Linting and formatting
lint:
	uv run ruff check .

lint-fix:
	uv run ruff check --fix .

format:
	uv run ruff format .
	uv run black .

format-check:
	uv run ruff format --check .
	uv run black --check .

# Type checking
type-check:
	uv run mypy .

# Run all CI checks locally
ci-local: lint format-check type-check test
	@echo "All CI checks passed!"

# Docker commands
docker-build:
	docker compose build

docker-up:
	docker compose up mcp-server-http

docker-up-sse:
	docker compose --profile sse up mcp-server-sse

docker-up-stdio:
	docker compose --profile stdio up mcp-server-stdio

docker-up-detached:
	docker compose up -d mcp-server-http

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f mcp-server-http

docker-clean:
	docker compose down -v
	docker system prune -f

# Clean build artifacts
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Run the server locally
run:
	uv run python main.py

run-http:
	MCP_PROTOCOL=http uv run python main.py

run-sse:
	MCP_PROTOCOL=sse uv run python main.py

run-stdio:
	MCP_PROTOCOL=stdio uv run python main.py
