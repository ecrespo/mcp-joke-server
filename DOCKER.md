# Docker Guide for MCP Joke Server

This guide explains how to run the MCP Joke Server using Docker and Docker Compose.

## Prerequisites

- Docker 20.10 or newer
- Docker Compose v2.0 or newer

## Quick Start

### Using Docker Compose (Recommended)

The project includes a `docker-compose.yml` file with pre-configured services for different MCP transport modes.

#### 1. Run HTTP Transport (Default)

```bash
docker compose up mcp-server-http
```

This starts the server on port 8000 with HTTP transport.

#### 2. Run SSE Transport

```bash
docker compose --profile sse up mcp-server-sse
```

This starts the server on port 8001 with SSE transport.

#### 3. Run Stdio Transport (for development)

```bash
docker compose --profile stdio up mcp-server-stdio
```

This starts the server with stdio transport (interactive mode).

### Run in Background (Detached Mode)

```bash
docker compose up -d mcp-server-http
```

### View Logs

```bash
docker compose logs -f mcp-server-http
```

### Stop Services

```bash
docker compose down
```

## Building the Docker Image

### Build using Docker Compose

```bash
docker compose build
```

### Build using Docker directly

```bash
docker build -t mcp-joke-server:latest .
```

## Authentication

The MCP server uses Bearer token authentication for HTTP and SSE transports. STDIO transport does not require authentication.

### Token Configuration

Set the `LOCAL_TOKEN` environment variable:

```env
LOCAL_TOKEN=your-secret-token-here
```

The default token in `docker-compose.yml` is: `-KB6aoXeiF-Qjor3LSEGh4-OOdJLCYrs5uqvUO9NCys`

### Testing Authentication

Test the server with authentication:

```bash
# Get the token from your .env file
TOKEN=$(grep LOCAL_TOKEN .env | cut -d= -f2)

# Make an authenticated request
curl -X POST http://localhost:8000/call-tool \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "tool_get_joke",
      "arguments": {}
    }
  }'
```

### Security Recommendations

- **Change the default token** in production
- **Use HTTPS** in production environments
- **Never commit** tokens to version control
- **Rotate tokens** periodically
- Use **Docker secrets** or environment variable files for sensitive data

## Running with Custom Configuration

### Using Environment Variables

Create a `.env.docker` file:

```env
API_BASE_URL=https://official-joke-api.appspot.com
LOCAL_TOKEN=your-custom-token-here
MCP_PROTOCOL=http
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
LOG_LEVEL=DEBUG
LOG_FILE=logs/mcp_server.log
```

Then run:

```bash
docker compose --env-file .env.docker up
```

### Using Docker Run

```bash
docker run -d \
  --name mcp-joke-server \
  -p 8000:8000 \
  -e API_BASE_URL=https://official-joke-api.appspot.com \
  -e LOCAL_TOKEN=your-secret-token-here \
  -e MCP_PROTOCOL=http \
  -e MCP_SERVER_HOST=0.0.0.0 \
  -e MCP_SERVER_PORT=8000 \
  -v $(pwd)/logs:/app/logs \
  mcp-joke-server:latest
```

## Health Checks

The Docker image includes a health check that runs every 30 seconds. You can check the health status with:

```bash
docker ps
docker inspect --format='{{.State.Health.Status}}' mcp-joke-server-http
```

## Volume Mounts

The `docker-compose.yml` file mounts the following volumes:

- `./logs:/app/logs` - Persists application logs on the host

## Network Configuration

All services are connected to a custom bridge network named `mcp-network`. This allows services to communicate with each other if needed.

## Troubleshooting

### Port Already in Use

If you get a port conflict error, either:

1. Stop the service using that port
2. Change the port mapping in `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"  # Map host port 8080 to container port 8000
```

### Permission Issues with Logs

If you encounter permission issues with the logs directory:

```bash
mkdir -p logs
chmod 755 logs
```

### Container Won't Start

Check the logs:

```bash
docker compose logs mcp-server-http
```

Verify environment variables are set correctly:

```bash
docker compose config
```

## Development Workflow

### Rebuild After Code Changes

```bash
docker compose build
docker compose up
```

### Run Tests in Container

```bash
docker compose run --rm mcp-server-http uv run pytest -v
```

### Access Container Shell

```bash
docker compose exec mcp-server-http /bin/bash
```

## Multi-Stage Build

The Dockerfile uses a multi-stage build to:

1. **Builder stage**: Install dependencies using uv
2. **Runtime stage**: Copy only necessary files and dependencies

This approach:
- Reduces final image size
- Improves build caching
- Enhances security by excluding build tools from runtime

## Image Size

The final image is based on `python:3.13-slim` and is optimized for production use. You can check the image size with:

```bash
docker images mcp-joke-server
```

## Production Deployment

For production deployments, consider:

1. **Use a reverse proxy** (nginx, traefik) for TLS termination
2. **Set resource limits** in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 512M
    reservations:
      cpus: '0.5'
      memory: 256M
```

3. **Use Docker secrets** for sensitive environment variables
4. **Enable monitoring** with Prometheus/Grafana
5. **Set up log aggregation** (ELK stack, Loki)

## CI/CD Integration

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:

1. Runs linting with Ruff
2. Checks code formatting with Black
3. Performs type checking with mypy
4. Runs tests with pytest
5. Builds the Docker image
6. Validates docker-compose configuration

The workflow runs on:
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

## Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastMCP Documentation](https://pypi.org/project/fastmcp/)
