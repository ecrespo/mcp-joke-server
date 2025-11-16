# MCP Joke Server - Architecture Diagrams

This document contains comprehensive architecture diagrams for the MCP Joke Server project using Mermaid notation.

## Table of Contents
1. [High-Level Architecture Overview](#high-level-architecture-overview)
2. [Component Diagram](#component-diagram)
3. [Transport Strategy Pattern](#transport-strategy-pattern)
4. [Repository Pattern Layers](#repository-pattern-layers)
5. [Data Flow Diagram](#data-flow-diagram)
6. [Class Hierarchy](#class-hierarchy)
7. [Sequence Diagram - Tool Execution](#sequence-diagram---tool-execution)

---

## High-Level Architecture Overview

This diagram shows the main architectural layers and their relationships.

```mermaid
graph TB
    subgraph "Entry Point Layer"
        MAIN[main.py<br/>FastMCP Server]
    end

    subgraph "Transport Strategy Layer"
        TS[TransportStrategy<br/>Interface]
        STDIO[StdioTransportStrategy]
        HTTP[HttpTransportStrategy]
        SSE[SseTransportStrategy]
        TSF[TransportStrategyFactory]
        TC[TransportConfig]
    end

    subgraph "Repository Layer"
        JR[JokeRepository<br/>Interface]
        CACHED[CachedJokeRepository<br/>Decorator]
        HTTPREPO[HTTPJokeRepository]
        RF[RepositoryFactory]
    end

    subgraph "HTTP Client Layer"
        API[JokeAPIClient<br/>Template Method]
        HTTPX[httpx Library]
    end

    subgraph "Configuration & Utils"
        SETTINGS[Settings<br/>Singleton]
        LOGGER[Logger Infrastructure]
        MODELS[Data Models<br/>Joke/Jokes]
        EXCEPT[Exception Hierarchy]
    end

    subgraph "External Services"
        EXT[External Joke API]
    end

    MAIN --> TSF
    TSF --> TS
    TS --> STDIO
    TS --> HTTP
    TS --> SSE
    STDIO --> TC
    HTTP --> TC
    SSE --> TC

    MAIN --> RF
    RF --> CACHED
    CACHED --> HTTPREPO
    HTTPREPO --> JR
    CACHED --> JR

    HTTPREPO --> API
    API --> HTTPX
    HTTPX --> EXT

    MAIN --> SETTINGS
    MAIN --> LOGGER
    API --> MODELS
    API --> EXCEPT

    style MAIN fill:#4CAF50
    style TS fill:#2196F3
    style JR fill:#FF9800
    style API fill:#9C27B0
    style SETTINGS fill:#F44336
```

---

## Component Diagram

This diagram shows the detailed component structure and their dependencies.

```mermaid
C4Component
    title Component Diagram - MCP Joke Server

    Container_Boundary(mcp, "MCP Joke Server") {
        Component(main, "Main Entry Point", "Python/FastMCP", "Initializes server and registers tools")

        Container_Boundary(transport, "Transport Strategies") {
            Component(tstrategy, "TransportStrategy", "Interface", "Abstract transport protocol")
            Component(stdio, "StdioTransportStrategy", "Concrete Strategy", "Subprocess communication")
            Component(http, "HttpTransportStrategy", "Concrete Strategy", "HTTP transport")
            Component(sse, "SseTransportStrategy", "Concrete Strategy", "Server-Sent Events")
            Component(tsfactory, "TransportStrategyFactory", "Factory", "Creates transport strategies")
        }

        Container_Boundary(repo, "Repository Layer") {
            Component(jrepo, "JokeRepository", "Interface", "Data access abstraction")
            Component(cached, "CachedJokeRepository", "Decorator", "TTL-based caching")
            Component(httprepo, "HTTPJokeRepository", "Repository", "HTTP-based implementation")
            Component(rfactory, "RepositoryFactory", "Factory", "Creates repositories")
        }

        Container_Boundary(client, "HTTP Client") {
            Component(apiclient, "JokeAPIClient", "Template Method", "Unified HTTP requests")
        }

        Container_Boundary(utils, "Utilities") {
            Component(settings, "Settings", "Singleton", "Application configuration")
            Component(models, "Data Models", "Dataclasses", "Joke/Jokes structures")
            Component(exceptions, "Exceptions", "Error Hierarchy", "Custom exceptions")
            Component(logger, "Logger", "Logging", "Structured logging")
        }
    }

    System_Ext(external, "External Joke API", "Third-party joke service")
    Person(user, "MCP Client", "Claude Desktop, etc.")

    Rel(user, main, "Calls tools via MCP")
    Rel(main, tsfactory, "Creates transport")
    Rel(tsfactory, tstrategy, "Instantiates")
    Rel(tstrategy, stdio, "")
    Rel(tstrategy, http, "")
    Rel(tstrategy, sse, "")

    Rel(main, rfactory, "Gets repository")
    Rel(rfactory, cached, "Creates")
    Rel(cached, httprepo, "Wraps")
    Rel(httprepo, apiclient, "Uses")
    Rel(apiclient, external, "HTTP requests")

    Rel(main, settings, "Reads config")
    Rel(apiclient, models, "Returns")
    Rel(apiclient, exceptions, "Throws")
    Rel(main, logger, "Logs events")
```

---

## Transport Strategy Pattern

This diagram illustrates the Strategy Pattern implementation for transport protocols.

```mermaid
classDiagram
    class TransportStrategy {
        <<abstract>>
        +logger: LoggerProtocol
        +transport_config: TransportConfig
        +get_transport_name() str*
        +get_transport_kwargs() dict*
        +prepare() None
        +validate() None
    }

    class TransportConfig {
        <<dataclass>>
        +transport_type: str
        +host: str
        +port: int
        +show_banner: bool
    }

    class StdioTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict
    }

    class HttpTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict
        +validate() None
        -_check_port_availability() bool
    }

    class SseTransportStrategy {
        +get_transport_name() str
        +get_transport_kwargs() dict
        +validate() None
        -_check_port_availability() bool
    }

    class TransportStrategyFactory {
        <<static>>
        +create_strategy(transport_type, logger) TransportStrategy
    }

    TransportStrategy <|-- StdioTransportStrategy
    TransportStrategy <|-- HttpTransportStrategy
    TransportStrategy <|-- SseTransportStrategy
    TransportStrategy --> TransportConfig : uses
    TransportStrategyFactory --> TransportStrategy : creates
    TransportStrategyFactory --> StdioTransportStrategy : instantiates
    TransportStrategyFactory --> HttpTransportStrategy : instantiates
    TransportStrategyFactory --> SseTransportStrategy : instantiates
```

---

## Repository Pattern Layers

This diagram shows the Repository and Decorator patterns for data access.

```mermaid
classDiagram
    class JokeRepository {
        <<abstract>>
        +get_random_joke() Joke*
        +get_random_jokes(count) Jokes*
        +get_joke_by_id(joke_id) Joke*
        +get_jokes_by_type(joke_type) Jokes*
        +health_check() bool*
    }

    class HTTPJokeRepository {
        -_client: JokeAPIClient
        -_logger: LoggerProtocol
        +get_random_joke() Joke
        +get_random_jokes(count) Jokes
        +get_joke_by_id(joke_id) Joke
        +get_jokes_by_type(joke_type) Jokes
        +health_check() bool
    }

    class CachedJokeRepository {
        -_repository: JokeRepository
        -_cache: dict
        -_cache_ttl: int
        -_stats: CacheStats
        +get_random_joke() Joke
        +get_random_jokes(count) Jokes
        +get_joke_by_id(joke_id) Joke
        +get_jokes_by_type(joke_type) Jokes
        +health_check() bool
        +get_cache_stats() CacheStats
        -_get_cached(key) Any
        -_set_cache(key, value) None
        -_should_cache(method) bool
    }

    class JokeAPIClient {
        -base_url: str
        -_logger: LoggerProtocol
        +get_joke() Joke
        +get_ten_jokes() Jokes
        +get_joke_by_id(joke_id) Joke
        +get_jokes_by_type(joke_type) Jokes
        +aget_joke() Joke
        +aget_ten_jokes() Jokes
        +aget_joke_by_id(joke_id) Joke
        +aget_jokes_by_type(joke_type) Jokes
        -_make_request(endpoint, parser) T
    }

    class RepositoryFactory {
        <<static>>
        +create_repository(logger) JokeRepository
    }

    JokeRepository <|-- HTTPJokeRepository
    JokeRepository <|-- CachedJokeRepository
    CachedJokeRepository --> JokeRepository : wraps
    HTTPJokeRepository --> JokeAPIClient : uses
    RepositoryFactory --> CachedJokeRepository : creates
    RepositoryFactory --> HTTPJokeRepository : creates
```

---

## Data Flow Diagram

This diagram illustrates the complete data flow from client request to response.

```mermaid
sequenceDiagram
    participant Client as MCP Client
    participant Main as main.py
    participant Tool as Tool Handler
    participant Cache as CachedJokeRepository
    participant HTTP as HTTPJokeRepository
    participant API as JokeAPIClient
    participant External as External Joke API

    Client->>Main: Call MCP Tool
    Main->>Tool: Execute tool_get_joke_by_id(5)
    Tool->>Cache: get_joke_by_id(5)

    alt Cache Hit
        Cache->>Cache: Check cache["joke:5"]
        Cache-->>Tool: Return cached Joke
    else Cache Miss
        Cache->>HTTP: get_joke_by_id(5)
        HTTP->>API: get_joke_by_id(5)
        API->>API: _make_request("/jokes/5", Joke parser)
        API->>External: httpx.get(API_BASE_URL + "/jokes/5")
        External-->>API: JSON Response
        API->>API: Parse to Joke dataclass
        API-->>HTTP: Return Joke
        HTTP-->>Cache: Return Joke
        Cache->>Cache: Store in cache["joke:5"]
        Cache-->>Tool: Return Joke
    end

    Tool->>Tool: extract_joke(joke.to_dict())
    Tool-->>Main: Return formatted string
    Main-->>Client: Return "setup\npunchline"
```

---

## Class Hierarchy

This diagram shows the complete class hierarchy and relationships.

```mermaid
classDiagram
    class Settings {
        <<Singleton>>
        +API_BASE_URL: str
        +MCP_PROTOCOL: str
        +MCP_SERVER_HOST: str
        +MCP_SERVER_PORT: int
        +LOG_LEVEL: str
        +get_instance() Settings
    }

    class Joke {
        <<frozen dataclass>>
        +type: str
        +setup: str
        +punchline: str
        +id: int
        +to_dict() dict
    }

    class Jokes {
        <<frozen dataclass>>
        +jokes: list~Joke~
        +get_jokes() list~Joke~
    }

    class JokeAPIError {
        <<Exception>>
        +message: str
    }

    class JokeAPITimeoutError {
        +timeout_seconds: float
    }

    class JokeAPIConnectionError {
        +original_error: Exception
    }

    class JokeAPIHTTPError {
        +status_code: int
    }

    class JokeAPIParseError {
        +response_text: str
    }

    class JokeRepositoryError {
        <<Exception>>
        +message: str
    }

    class JokeNotFoundError {
        +joke_id: int
    }

    JokeAPIError <|-- JokeAPITimeoutError
    JokeAPIError <|-- JokeAPIConnectionError
    JokeAPIError <|-- JokeAPIHTTPError
    JokeAPIError <|-- JokeAPIParseError
    JokeRepositoryError <|-- JokeNotFoundError

    Jokes --> Joke : contains
```

---

## Sequence Diagram - Tool Execution

Complete sequence diagram showing a full tool execution flow with all components.

```mermaid
sequenceDiagram
    autonumber
    participant Client as MCP Client
    participant FastMCP as FastMCP Server
    participant Main as main.py
    participant Factory as RepositoryFactory
    participant Cache as CachedJokeRepository
    participant HTTPRepo as HTTPJokeRepository
    participant APIClient as JokeAPIClient
    participant httpx as httpx Library
    participant External as External API
    participant Logger as Logger

    Note over Client,External: Initialization Phase
    Client->>FastMCP: Initialize Connection
    FastMCP->>Main: Start Server
    Main->>Factory: get_joke_repository()
    Factory->>HTTPRepo: Create HTTPJokeRepository
    Factory->>Cache: Create CachedJokeRepository(HTTPRepo)
    Factory-->>Main: Return repository instance

    Note over Client,External: Tool Execution Phase
    Client->>FastMCP: tool_get_joke_by_id(joke_id=5)
    FastMCP->>Main: Route to tool handler
    Main->>Logger: Log tool call
    Main->>Cache: get_joke_by_id(5)

    alt Cache contains joke:5
        Cache->>Logger: Log cache hit
        Cache-->>Main: Return Joke from cache
    else Cache does not contain joke:5
        Cache->>Logger: Log cache miss
        Cache->>HTTPRepo: get_joke_by_id(5)
        HTTPRepo->>Logger: Log repository call
        HTTPRepo->>APIClient: get_joke_by_id(5)
        APIClient->>Logger: Log API request
        APIClient->>httpx: get("/jokes/5")
        httpx->>External: HTTP GET Request

        alt Successful Response
            External-->>httpx: 200 OK + JSON
            httpx-->>APIClient: Response object
            APIClient->>APIClient: Parse JSON to Joke
            APIClient->>Logger: Log success
            APIClient-->>HTTPRepo: Return Joke
            HTTPRepo-->>Cache: Return Joke
            Cache->>Cache: Store in cache["joke:5"]
            Cache->>Logger: Log cache store
            Cache-->>Main: Return Joke
        else Error Response
            External-->>httpx: 4xx/5xx Error
            httpx-->>APIClient: Error response
            APIClient->>APIClient: Raise JokeAPIHTTPError
            APIClient->>Logger: Log error
            APIClient-->>HTTPRepo: Raise exception
            HTTPRepo->>HTTPRepo: Convert to JokeRepositoryError
            HTTPRepo-->>Cache: Raise exception
            Cache-->>Main: Raise exception
            Main->>Logger: Log error
            Main-->>FastMCP: Error response
            FastMCP-->>Client: Error message
        end
    end

    Main->>Main: extract_joke(joke.to_dict())
    Main-->>FastMCP: Return formatted joke
    FastMCP-->>Client: Display joke to user
```

---

## Design Patterns Summary

```mermaid
mindmap
    root((MCP Joke Server<br/>Design Patterns))
        Strategy Pattern
            TransportStrategy
            StdioTransportStrategy
            HttpTransportStrategy
            SseTransportStrategy
            Purpose: Transport protocol abstraction
        Repository Pattern
            JokeRepository Interface
            HTTPJokeRepository
            Data access abstraction
            Testability
        Decorator Pattern
            CachedJokeRepository
            Transparent caching
            Composable behavior
        Factory Pattern
            TransportStrategyFactory
            RepositoryFactory
            Object creation
            Dependency management
        Template Method
            JokeAPIClient
            _make_request method
            Unified error handling
        Singleton Pattern
            Settings metaclass
            get_joke_repository
            Single instance
        Dependency Injection
            Logger injection
            Repository injection
            Loose coupling
```

---

## Legend

### Diagram Types
- **Graph TB**: Top-Bottom flow diagrams
- **Class Diagram**: UML class relationships
- **Sequence Diagram**: Interaction flows
- **Mind Map**: Conceptual relationships

### Color Coding (High-Level Architecture)
- 🟢 Green: Entry points (main.py)
- 🔵 Blue: Strategy layer (Transport)
- 🟠 Orange: Repository layer
- 🟣 Purple: HTTP client layer
- 🔴 Red: Configuration

### Relationship Symbols
- `-->`: Uses/depends on
- `<|--`: Inherits from/implements
- `*`: Abstract method

---

## Quick Reference

### Main Components
1. **main.py**: FastMCP server entry point with 7 tools
2. **strategies/**: Transport protocol implementations (stdio, HTTP, SSE)
3. **repositories/**: Data access layer with caching
4. **utils/RequestAPIJokes.py**: HTTP client for external API
5. **utils/config.py**: Centralized configuration management
6. **utils/model.py**: Data structures (Joke, Jokes)
7. **utils/exceptions.py**: Custom exception hierarchy

### Key Extension Points
- Add new transport: Extend `TransportStrategy`
- Add new repository: Implement `JokeRepository`
- Customize caching: Modify `CachedJokeRepository`
- Add async tools: Use `aget_*` methods

---

*Generated on 2025-11-15*
