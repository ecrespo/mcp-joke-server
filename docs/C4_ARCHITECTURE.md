# MCP Joke Server - C4 Architecture Model

This document provides a complete C4 Model architecture documentation for the MCP Joke Server project. The C4 model uses four levels of abstraction: Context, Container, Component, and Code.

## Table of Contents
1. [Level 1: System Context Diagram](#level-1-system-context-diagram)
2. [Level 2: Container Diagram](#level-2-container-diagram)
3. [Level 3: Component Diagram](#level-3-component-diagram)
   - [Transport Strategy Components](#transport-strategy-components)
   - [Repository Components](#repository-components)
   - [HTTP Client Components](#http-client-components)
4. [Level 4: Code Diagrams](#level-4-code-diagrams)
   - [Transport Strategy Classes](#transport-strategy-classes)
   - [Repository Pattern Classes](#repository-pattern-classes)
   - [Data Models](#data-models)
   - [Exception Hierarchy](#exception-hierarchy)

---

## Level 1: System Context Diagram

The highest level view showing the MCP Joke Server system and its interactions with users and external systems.

```mermaid
C4Context
    title System Context - MCP Joke Server

    Person(user, "User", "Developer or end-user using Claude Desktop or other MCP clients")

    System(mcpServer, "MCP Joke Server", "Provides joke retrieval tools via Model Context Protocol. Supports multiple transport protocols (stdio, HTTP, SSE) and implements caching for performance.")

    System_Ext(externalAPI, "External Joke API", "Third-party REST API providing joke data with various endpoints for random jokes, specific jokes by ID, and jokes filtered by type.")

    System_Ext(mcpClient, "MCP Client", "Claude Desktop, custom MCP clients, or other applications that consume MCP tools.")

    Rel(user, mcpClient, "Interacts with", "Natural language, UI")
    Rel(mcpClient, mcpServer, "Calls joke tools", "MCP Protocol (stdio/HTTP/SSE)")
    Rel(mcpServer, externalAPI, "Fetches jokes", "HTTPS/REST")

    UpdateRelStyle(user, mcpClient, $offsetY="-40", $offsetX="-50")
    UpdateRelStyle(mcpClient, mcpServer, $offsetY="-20")
    UpdateRelStyle(mcpServer, externalAPI, $offsetY="-20")
```

### System Purpose

**MCP Joke Server** is a Model Context Protocol server that:
- Exposes 7 joke retrieval tools (4 synchronous + 3 asynchronous variants)
- Supports flexible transport protocols for different deployment scenarios
- Implements intelligent caching to reduce external API calls
- Provides structured error handling and logging
- Follows clean architecture principles with separation of concerns

### Key System Characteristics
- **Protocol Support**: stdio (subprocess), HTTP (network), SSE (streaming)
- **Caching Strategy**: TTL-based in-memory cache (5-minute default)
- **API Integration**: REST client with retry logic and error handling
- **Configuration**: Environment-based settings with validation
- **Logging**: Structured logging with Rich console formatting

---

## Level 2: Container Diagram

Shows the high-level technology choices and how containers communicate.

```mermaid
C4Container
    title Container Diagram - MCP Joke Server

    Person(user, "User", "Developer using MCP client")

    System_Boundary(mcp_boundary, "MCP Joke Server") {
        Container(fastmcp, "FastMCP Server", "Python/FastMCP", "MCP protocol server exposing joke retrieval tools")
        Container(transport, "Transport Layer", "Python/Strategy Pattern", "Handles protocol-specific communication (stdio/HTTP/SSE)")
        Container(repository, "Repository Layer", "Python/Repository Pattern", "Abstracts data access with caching decorator")
        Container(httpClient, "HTTP Client", "Python/httpx", "Manages external API communication with retry logic")
        Container(config, "Configuration", "Python/Pydantic", "Centralized settings management")
        ContainerDb(cache, "In-Memory Cache", "Python dict", "TTL-based joke cache")
    }

    System_Ext(mcpClient, "MCP Client", "Claude Desktop, custom clients")
    System_Ext(externalAPI, "External Joke API", "REST API")

    Rel(user, mcpClient, "Uses")
    Rel(mcpClient, fastmcp, "Calls tools", "MCP (stdio/HTTP/SSE)")
    Rel(fastmcp, transport, "Initializes", "Factory pattern")
    Rel(fastmcp, repository, "Calls methods", "Python API")
    Rel(repository, cache, "Reads/Writes", "Cache operations")
    Rel(repository, httpClient, "Delegates to", "Method calls")
    Rel(httpClient, externalAPI, "HTTP requests", "HTTPS/REST")
    Rel(config, fastmcp, "Provides settings", "Singleton")
    Rel(config, transport, "Provides config")
    Rel(config, httpClient, "Provides base URL")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Container Responsibilities

| Container | Technology | Responsibility |
|-----------|-----------|----------------|
| **FastMCP Server** | Python, FastMCP library | Tool registration, request routing, response formatting |
| **Transport Layer** | Python, Strategy Pattern | Protocol abstraction, connection management, validation |
| **Repository Layer** | Python, Repository + Decorator Pattern | Data access abstraction, caching logic, error mapping |
| **HTTP Client** | Python, httpx | External API communication, request/response handling, retry logic |
| **Configuration** | Pydantic BaseSettings | Environment-based config, validation, singleton access |
| **In-Memory Cache** | Python dict | Temporary storage for deterministic queries, TTL management |

### Inter-Container Communication

1. **MCP Client → FastMCP**: Protocol-specific transport (stdio/HTTP/SSE)
2. **FastMCP → Repository**: Direct Python method calls
3. **Repository → Cache**: Dictionary operations with TTL checking
4. **Repository → HTTP Client**: Method delegation for cache misses
5. **HTTP Client → External API**: HTTPS REST requests
6. **Configuration → All**: Injected settings via singleton pattern

---

## Level 3: Component Diagram

### Main Application Components

```mermaid
C4Component
    title Component Diagram - Main Application Layer

    Container_Boundary(app, "FastMCP Server Application") {
        Component(main, "main.py", "Python Module", "Server initialization, tool registration, dependency wiring")
        Component(tools, "Tool Handlers", "Python Functions", "7 MCP tools: get_joke, get_ten_jokes, get_joke_by_id, get_jokes_by_type + async variants")
        Component(extractors, "Data Extractors", "Utility Functions", "extract_joke, extract_jokes - format data for display")
    }

    Container_Boundary(transport_container, "Transport Layer") {
        Component(tStrategy, "TransportStrategy", "Abstract Base", "Interface for transport implementations")
        Component(tFactory, "TransportStrategyFactory", "Factory", "Creates transport instances")
        Component(tConfig, "TransportConfig", "Dataclass", "Immutable transport configuration")
        Component(stdio, "StdioTransportStrategy", "Concrete Strategy", "Subprocess transport")
        Component(http, "HttpTransportStrategy", "Concrete Strategy", "HTTP network transport")
        Component(sse, "SseTransportStrategy", "Concrete Strategy", "Server-Sent Events transport")
    }

    Container_Boundary(repo_container, "Repository Layer") {
        Component(jRepo, "JokeRepository", "Abstract Base", "Data access interface")
        Component(rFactory, "RepositoryFactory", "Factory", "Creates repository instances")
        Component(httpRepo, "HTTPJokeRepository", "Concrete Repository", "HTTP-based implementation")
        Component(cachedRepo, "CachedJokeRepository", "Decorator", "Adds caching behavior")
    }

    Container_Boundary(client_container, "HTTP Client Layer") {
        Component(apiClient, "JokeAPIClient", "API Client", "Template method pattern for API calls")
        Component(httpxLib, "httpx", "External Library", "HTTP client library")
    }

    Container_Boundary(utils_container, "Utilities & Configuration") {
        Component(settings, "Settings", "Singleton", "Application configuration")
        Component(models, "Data Models", "Dataclasses", "Joke, Jokes structures")
        Component(exceptions, "Exceptions", "Error Classes", "Custom exception hierarchy")
        Component(logger, "Logger", "Logging Infrastructure", "Structured logging with Rich")
        Component(constants, "Constants", "Module", "JOKE_TYPES, URLs")
    }

    System_Ext(external, "External Joke API", "REST API")
    Person(client, "MCP Client")

    Rel(client, main, "Calls via MCP")
    Rel(main, tools, "Routes requests")
    Rel(main, tFactory, "Creates transport")
    Rel(tFactory, tStrategy, "Instantiates")
    Rel(tStrategy, stdio, "")
    Rel(tStrategy, http, "")
    Rel(tStrategy, sse, "")
    Rel(stdio, tConfig, "Uses")
    Rel(http, tConfig, "Uses")
    Rel(sse, tConfig, "Uses")

    Rel(tools, rFactory, "Gets repository")
    Rel(rFactory, cachedRepo, "Creates")
    Rel(cachedRepo, jRepo, "Implements")
    Rel(cachedRepo, httpRepo, "Wraps")
    Rel(httpRepo, jRepo, "Implements")
    Rel(tools, extractors, "Formats data")

    Rel(httpRepo, apiClient, "Uses")
    Rel(apiClient, httpxLib, "HTTP calls")
    Rel(httpxLib, external, "HTTPS requests")

    Rel(main, settings, "Reads config")
    Rel(tConfig, settings, "Reads config")
    Rel(apiClient, settings, "Reads base URL")
    Rel(apiClient, models, "Returns")
    Rel(apiClient, exceptions, "Raises")
    Rel(main, logger, "Logs")
    Rel(httpRepo, logger, "Logs")
    Rel(apiClient, logger, "Logs")
    Rel(tools, constants, "Validates types")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Transport Strategy Components

```mermaid
C4Component
    title Component Diagram - Transport Strategy Layer (Detailed)

    Container_Boundary(strategies, "Transport Strategies Package") {
        Component(base, "TransportStrategy", "ABC", "Abstract base with prepare(), validate(), get_transport_name(), get_transport_kwargs()")

        Component(stdio_impl, "StdioTransportStrategy", "Concrete Class", "Returns 'stdio' transport config with show_banner setting")

        Component(http_impl, "HttpTransportStrategy", "Concrete Class", "Returns 'streamable-http' config, validates port availability")

        Component(sse_impl, "SseTransportStrategy", "Concrete Class", "Returns 'sse' config, validates port availability")

        Component(factory, "TransportStrategyFactory", "Static Factory", "Maps transport_type string to strategy class")

        Component(config_dc, "TransportConfig", "Frozen Dataclass", "transport_type, host, port, show_banner fields")

        Component(validator, "Port Validator", "Utility", "Checks port availability using socket")
    }

    Container(settings, "Settings", "Singleton", "Provides MCP_PROTOCOL, MCP_SERVER_HOST, MCP_SERVER_PORT")

    Container(logger, "Logger", "Logging", "Injected for structured logging")

    Rel(factory, base, "Returns instance of")
    Rel(base, stdio_impl, "Implemented by")
    Rel(base, sse_impl, "Implemented by")
    Rel(base, http_impl, "Implemented by")

    Rel(stdio_impl, config_dc, "Uses")
    Rel(http_impl, config_dc, "Uses")
    Rel(sse_impl, config_dc, "Uses")

    Rel(http_impl, validator, "Calls _check_port_availability()")
    Rel(sse_impl, validator, "Calls _check_port_availability()")

    Rel(config_dc, settings, "Reads from")
    Rel(base, logger, "Logs events")

    UpdateLayoutConfig($c4ShapeInRow="3")
```

**Key Design Decisions:**
- **Strategy Pattern**: Enables runtime transport selection without changing core logic
- **Validation**: HTTP and SSE strategies validate port availability before startup
- **Immutability**: TransportConfig is frozen to prevent accidental modification
- **Factory**: Centralizes strategy creation with error handling for unknown types

### Repository Components

```mermaid
C4Component
    title Component Diagram - Repository Layer (Detailed)

    Container_Boundary(repositories, "Repositories Package") {
        Component(repo_interface, "JokeRepository", "ABC", "Abstract interface: 5 methods (get_random_joke, get_random_jokes, get_joke_by_id, get_jokes_by_type, health_check)")

        Component(http_repo, "HTTPJokeRepository", "Concrete Repository", "Delegates to JokeAPIClient, maps exceptions to repository errors")

        Component(cached_repo, "CachedJokeRepository", "Decorator", "Wraps any JokeRepository, adds TTL-based caching with statistics")

        Component(cache_stats, "CacheStats", "Dataclass", "Tracks hits, misses, evictions, hit_rate")

        Component(repo_factory, "RepositoryFactory", "Static Factory", "Creates default cached repository composition")

        Component(singleton_getter, "get_joke_repository()", "Function", "Singleton accessor for repository instance")
    }

    Component(api_client, "JokeAPIClient", "HTTP Client", "Template method pattern for API calls")

    Component(logger, "Logger", "Logging", "Injected dependency")

    Component(models, "Joke/Jokes", "Dataclasses", "Return types")

    Component(exceptions, "JokeRepositoryError", "Exception", "Repository-level errors")

    Rel(repo_factory, cached_repo, "Creates")
    Rel(repo_factory, http_repo, "Creates")
    Rel(cached_repo, repo_interface, "Implements")
    Rel(http_repo, repo_interface, "Implements")
    Rel(cached_repo, http_repo, "Wraps")
    Rel(singleton_getter, repo_factory, "Calls create_repository()")

    Rel(cached_repo, cache_stats, "Maintains")
    Rel(http_repo, api_client, "Uses")
    Rel(http_repo, logger, "Logs")
    Rel(cached_repo, logger, "Logs")

    Rel(http_repo, models, "Returns")
    Rel(cached_repo, models, "Returns")
    Rel(http_repo, exceptions, "Raises")

    UpdateLayoutConfig($c4ShapeInRow="3")
```

**Key Design Decisions:**
- **Repository Pattern**: Abstracts data source, enabling easy mocking in tests
- **Decorator Pattern**: CachedJokeRepository transparently adds caching without changing interface
- **Smart Caching**: Only caches deterministic queries (by_id, by_type), not random jokes
- **Statistics**: Cache maintains metrics for observability
- **Error Mapping**: HTTPJokeRepository converts API exceptions to repository exceptions

### HTTP Client Components

```mermaid
C4Component
    title Component Diagram - HTTP Client Layer (Detailed)

    Container_Boundary(client, "HTTP Client Package") {
        Component(api_client, "JokeAPIClient", "API Client Class", "Template method pattern: _make_request() centralizes logic")

        Component(sync_methods, "Synchronous Methods", "Methods", "get_joke(), get_ten_jokes(), get_joke_by_id(), get_jokes_by_type()")

        Component(async_methods, "Asynchronous Methods", "Async Methods", "aget_joke(), aget_ten_jokes(), aget_joke_by_id(), aget_jokes_by_type()")

        Component(template_method, "_make_request()", "Template Method", "Unified request handling with error mapping and logging")

        Component(parsers, "Response Parsers", "Type Functions", "Callable[[dict], T] for Joke and Jokes parsing")
    }

    Component(httpx_sync, "httpx.Client", "HTTP Library", "Synchronous HTTP client")
    Component(httpx_async, "httpx.AsyncClient", "HTTP Library", "Asynchronous HTTP client")

    Component(models, "Joke/Jokes", "Dataclasses", "Parsed response models")

    Component(exceptions, "JokeAPIError hierarchy", "Exceptions", "Timeout, Connection, HTTP, Parse errors")

    Component(logger, "Logger", "Logging", "Request/response logging")

    Component(settings, "Settings", "Config", "API_BASE_URL")

    System_Ext(external, "External Joke API", "REST endpoints")

    Rel(sync_methods, template_method, "Calls")
    Rel(async_methods, template_method, "Calls (async variant)")
    Rel(template_method, parsers, "Uses for response parsing")

    Rel(template_method, httpx_sync, "Sync requests")
    Rel(template_method, httpx_async, "Async requests")

    Rel(httpx_sync, external, "GET requests")
    Rel(httpx_async, external, "GET requests")

    Rel(template_method, models, "Returns")
    Rel(template_method, exceptions, "Raises on error")
    Rel(template_method, logger, "Logs requests/responses")

    Rel(api_client, settings, "Reads API_BASE_URL")

    UpdateLayoutConfig($c4ShapeInRow="2")
```

**Key Design Decisions:**
- **Template Method**: `_make_request()` eliminates code duplication across 8 methods
- **Dual Mode**: Both sync and async variants for different use cases
- **Error Handling**: Comprehensive exception mapping (timeout, connection, HTTP, parse)
- **Type Safety**: Generic type parameter T with parser functions
- **Logging**: Structured logging of all requests and responses

---

## Level 4: Code Diagrams

### Transport Strategy Classes

```mermaid
classDiagram
    class TransportStrategy {
        <<abstract>>
        +logger: LoggerProtocol
        +transport_config: TransportConfig
        +__init__(logger: LoggerProtocol)
        +get_transport_name() str*
        +get_transport_kwargs() dict~str, Any~*
        +prepare() None
        +validate() None
        #_load_config() TransportConfig
    }

    class TransportConfig {
        <<frozen dataclass>>
        +transport_type: str
        +host: str
        +port: int
        +show_banner: bool
        +__post_init__() None
    }

    class StdioTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict~str, Any~
    }

    class HttpTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict~str, Any~
        +validate() None
        -_check_port_availability() bool
    }

    class SseTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict~str, Any~
        +validate() None
        -_check_port_availability() bool
    }

    class TransportStrategyFactory {
        <<static>>
        +_strategies: dict~str, Type[TransportStrategy]~
        +create_strategy(transport_type: str, logger: LoggerProtocol) TransportStrategy$
        +register_strategy(name: str, strategy_class: Type[TransportStrategy]) None$
    }

    class LoggerProtocol {
        <<protocol>>
        +info(msg: str) None
        +error(msg: str) None
        +debug(msg: str) None
        +warning(msg: str) None
    }

    TransportStrategy <|-- StdioTransportStrategy : implements
    TransportStrategy <|-- HttpTransportStrategy : implements
    TransportStrategy <|-- SseTransportStrategy : implements
    TransportStrategy --> TransportConfig : uses
    TransportStrategy --> LoggerProtocol : depends on
    TransportStrategyFactory ..> TransportStrategy : creates
    TransportStrategyFactory --> StdioTransportStrategy : instantiates
    TransportStrategyFactory --> HttpTransportStrategy : instantiates
    TransportStrategyFactory --> SseTransportStrategy : instantiates

    note for TransportStrategy "Template method pattern:\nprepare() orchestrates logging\nand delegates to abstract methods"

    note for TransportStrategyFactory "Registry pattern:\nStrategies registered in _strategies dict\nSupports extension without modification"
```

**Implementation Details:**

```python
# Abstract method examples
class TransportStrategy(ABC):
    @abstractmethod
    def get_transport_name(self) -> str:
        """Returns the transport protocol name"""
        pass

    @abstractmethod
    def get_transport_kwargs(self) -> dict[str, Any]:
        """Returns FastMCP transport configuration"""
        pass

# Concrete implementation example
class HttpTransportStrategy(TransportStrategy):
    def get_transport_name(self) -> str:
        return "streamable-http"

    def get_transport_kwargs(self) -> dict[str, Any]:
        return {
            "transport": "streamable-http",
            "http_server_host": self.transport_config.host,
            "http_server_port": self.transport_config.port
        }
```

### Repository Pattern Classes

```mermaid
classDiagram
    class JokeRepository {
        <<abstract>>
        +get_random_joke() Joke*
        +get_random_jokes(count: int) Jokes*
        +get_joke_by_id(joke_id: int) Joke*
        +get_jokes_by_type(joke_type: str) Jokes*
        +health_check() bool*
    }

    class HTTPJokeRepository {
        -_client: JokeAPIClient
        -_logger: LoggerProtocol
        +__init__(client: JokeAPIClient, logger: LoggerProtocol)
        +get_random_joke() Joke
        +get_random_jokes(count: int) Jokes
        +get_joke_by_id(joke_id: int) Joke
        +get_jokes_by_type(joke_type: str) Jokes
        +health_check() bool
        -_handle_api_error(error: JokeAPIError) None
    }

    class CachedJokeRepository {
        -_repository: JokeRepository
        -_cache: dict~str, tuple[Any, float]~
        -_cache_ttl: int
        -_stats: CacheStats
        -_logger: LoggerProtocol
        +__init__(repository: JokeRepository, cache_ttl: int, logger: LoggerProtocol)
        +get_random_joke() Joke
        +get_random_jokes(count: int) Jokes
        +get_joke_by_id(joke_id: int) Joke
        +get_jokes_by_type(joke_type: str) Jokes
        +health_check() bool
        +get_cache_stats() CacheStats
        +clear_cache() None
        -_get_cached(key: str) Any | None
        -_set_cache(key: str, value: Any) None
        -_should_cache(method_name: str) bool
        -_is_expired(timestamp: float) bool
        -_evict_expired() None
    }

    class CacheStats {
        <<dataclass>>
        +hits: int = 0
        +misses: int = 0
        +evictions: int = 0
        +hit_rate() float
    }

    class RepositoryFactory {
        <<static>>
        +create_repository(logger: LoggerProtocol, cache_ttl: int) JokeRepository$
        +create_http_repository(logger: LoggerProtocol) HTTPJokeRepository$
        +create_cached_repository(repository: JokeRepository, cache_ttl: int, logger: LoggerProtocol) CachedJokeRepository$
    }

    class JokeAPIClient {
        -base_url: str
        -_logger: LoggerProtocol
        +get_joke() Joke
        +get_ten_jokes() Jokes
        +get_joke_by_id(joke_id: int) Joke
        +get_jokes_by_type(joke_type: str) Jokes
        +aget_joke() Joke
        +aget_ten_jokes() Jokes
        +aget_joke_by_id(joke_id: int) Joke
        +aget_jokes_by_type(joke_type: str) Jokes
        -_make_request(endpoint: str, parser: Callable) T
    }

    JokeRepository <|.. HTTPJokeRepository : implements
    JokeRepository <|.. CachedJokeRepository : implements
    CachedJokeRepository o-- JokeRepository : wraps
    CachedJokeRepository *-- CacheStats : owns
    HTTPJokeRepository --> JokeAPIClient : uses
    RepositoryFactory ..> JokeRepository : creates
    RepositoryFactory ..> HTTPJokeRepository : creates
    RepositoryFactory ..> CachedJokeRepository : creates

    note for CachedJokeRepository "Decorator pattern:\nTransparently adds caching\nto any JokeRepository implementation"

    note for RepositoryFactory "Default composition:\nCachedJokeRepository wrapping\nHTTPJokeRepository"
```

**Cache Key Strategy:**
```python
# Deterministic queries (cached)
"joke:{joke_id}"           # get_joke_by_id(5) → "joke:5"
"jokes:type:{joke_type}"   # get_jokes_by_type("general") → "jokes:type:general"

# Non-deterministic queries (not cached)
get_random_joke()          # Different result each call
get_random_jokes(count)    # Different results each call
```

### Data Models

```mermaid
classDiagram
    class Joke {
        <<frozen dataclass>>
        +type: str
        +setup: str
        +punchline: str
        +id: int
        +to_dict() dict~str, Any~
        +get_type() str
        +get_setup() str
        +get_punchline() str
        +get_id() int
        +__str__() str
        +__repr__() str
    }

    class Jokes {
        <<frozen dataclass>>
        +jokes: list~Joke~
        +get_jokes() list~Joke~
        +__len__() int
        +__iter__() Iterator~Joke~
        +__getitem__(index: int) Joke
        +__str__() str
        +__repr__() str
    }

    class Settings {
        <<Singleton>>
        +API_BASE_URL: str
        +MCP_PROTOCOL: str
        +MCP_SERVER_HOST: str
        +MCP_SERVER_PORT: int
        +LOG_LEVEL: str
        +LOG_FORMAT: str
        +SESSION_TIMEOUT: int
        +get_instance() Settings$
        -_validate_url(value: str) str
        -_validate_protocol(value: str) str
        -_validate_port(value: int) int
    }

    class TransportConfig {
        <<frozen dataclass>>
        +transport_type: str
        +host: str
        +port: int
        +show_banner: bool
        +__post_init__() None
    }

    Jokes o-- Joke : contains

    note for Joke "Immutable data structure\nfor single joke representation"

    note for Jokes "Collection wrapper with\niterator protocol support"

    note for Settings "Singleton via metaclass\nPydantic validation"
```

### Exception Hierarchy

```mermaid
classDiagram
    class Exception {
        <<built-in>>
    }

    class JokeAPIError {
        +message: str
        +__init__(message: str)
        +__str__() str
    }

    class JokeAPITimeoutError {
        +timeout_seconds: float
        +__init__(message: str, timeout_seconds: float)
    }

    class JokeAPIConnectionError {
        +original_error: Exception
        +__init__(message: str, original_error: Exception)
    }

    class JokeAPIHTTPError {
        +status_code: int
        +__init__(message: str, status_code: int)
    }

    class JokeAPIParseError {
        +response_text: str
        +__init__(message: str, response_text: str)
    }

    class JokeRepositoryError {
        +message: str
        +__init__(message: str)
        +__str__() str
    }

    class JokeNotFoundError {
        +joke_id: int
        +__init__(joke_id: int)
    }

    Exception <|-- JokeAPIError
    JokeAPIError <|-- JokeAPITimeoutError
    JokeAPIError <|-- JokeAPIConnectionError
    JokeAPIError <|-- JokeAPIHTTPError
    JokeAPIError <|-- JokeAPIParseError

    Exception <|-- JokeRepositoryError
    JokeRepositoryError <|-- JokeNotFoundError

    note for JokeAPIError "API layer exceptions\nRaised by JokeAPIClient"

    note for JokeRepositoryError "Repository layer exceptions\nMapped from API errors"
```

**Exception Flow:**
```
External API Error
    ↓
JokeAPIClient catches
    ↓
Raises JokeAPI*Error (specific type)
    ↓
HTTPJokeRepository catches
    ↓
Maps to JokeRepositoryError
    ↓
Propagates to Tool Handler
    ↓
Returns error to MCP Client
```

---

## C4 Model Summary

### Level 1: Context
- **Focus**: System boundary and external interactions
- **Audience**: Everyone (technical and non-technical)
- **Shows**: MCP Joke Server, users, external systems

### Level 2: Container
- **Focus**: High-level technology choices
- **Audience**: Technical people (developers, architects)
- **Shows**: FastMCP server, transport layer, repository, HTTP client, cache

### Level 3: Component
- **Focus**: Internal structure of containers
- **Audience**: Developers and architects
- **Shows**: Strategy factories, repository decorators, API clients, utilities

### Level 4: Code
- **Focus**: Implementation details
- **Audience**: Developers
- **Shows**: Class diagrams, method signatures, relationships

---

## Design Patterns by C4 Level

| Pattern | C4 Level | Location | Purpose |
|---------|----------|----------|---------|
| **Strategy** | 3 & 4 | Transport Layer | Runtime protocol selection |
| **Repository** | 2 & 3 & 4 | Data Access | Abstract data source |
| **Decorator** | 3 & 4 | CachedJokeRepository | Add caching behavior |
| **Factory** | 3 & 4 | Multiple factories | Object creation |
| **Template Method** | 4 | JokeAPIClient | Unified request handling |
| **Singleton** | 2 & 4 | Settings, repository getter | Single instance |
| **Dependency Injection** | 2 & 3 | Throughout | Loose coupling |

---

## Navigation Guide

### For Architects
1. Start with **Level 1** for system overview
2. Review **Level 2** for technology choices
3. Examine **Level 3** for component interactions

### For Developers
1. Review **Level 2** for container responsibilities
2. Dive into **Level 3** for component details
3. Study **Level 4** for implementation specifics

### For New Team Members
1. **Level 1**: Understand the system purpose
2. **Level 2**: Learn the technology stack
3. **Level 3**: Explore component structure
4. **Level 4**: Study code patterns and conventions

---

## Extension Points by Level

### Container Level (L2)
- Add new transport container (e.g., WebSocket)
- Replace cache container (e.g., Redis)
- Add monitoring container

### Component Level (L3)
- New transport strategy (extend TransportStrategy)
- New repository implementation (implement JokeRepository)
- Custom cache policy (extend CachedJokeRepository)

### Code Level (L4)
- Add new API endpoints (extend JokeAPIClient)
- Custom exception types (extend JokeAPIError)
- Additional data models (new dataclasses)

---

## References

- **C4 Model**: https://c4model.com/
- **Mermaid C4 Diagrams**: https://mermaid.js.org/syntax/c4.html
- **FastMCP Documentation**: https://github.com/jlowin/fastmcp
- **Repository Pattern**: https://martinfowler.com/eaaCatalog/repository.html
- **Strategy Pattern**: https://refactoring.guru/design-patterns/strategy

---

*Generated on 2025-11-15*
*MCP Joke Server - C4 Architecture Model v1.0*
