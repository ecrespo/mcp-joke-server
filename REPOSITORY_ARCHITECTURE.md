# Repository Pattern - Arquitectura Visual

## Diagrama de Clases

```
┌─────────────────────────────────────────────────────────────────────┐
│                      <<interface>>                                   │
│                     JokeRepository                                   │
├─────────────────────────────────────────────────────────────────────┤
│ + get_random_joke() -> Joke                                         │
│ + get_random_jokes(count: int) -> Jokes                             │
│ + get_joke_by_id(joke_id: int) -> Joke                              │
│ + get_jokes_by_type(joke_type: JOKE_TYPES) -> Jokes                 │
│ + health_check() -> bool                                            │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          │ implements
         ┌────────────────┴────────────────┐
         │                                  │
         ▼                                  ▼
┌──────────────────────┐      ┌──────────────────────────────┐
│ HTTPJokeRepository   │      │  CachedJokeRepository        │
├──────────────────────┤      ├──────────────────────────────┤
│ - _client            │      │ - _repository: JokeRepository│
├──────────────────────┤      │ - _cache: dict               │
│ + get_random_joke()  │      │ - _default_ttl: int          │
│ + get_joke_by_id()   │      │ - _stats: dict               │
│ + get_jokes_by_type()│      ├──────────────────────────────┤
│ + health_check()     │      │ + get_random_joke()          │
└──────────────────────┘      │ + get_joke_by_id()           │
                              │ + get_jokes_by_type()        │
                              │ + health_check()             │
                              │ + clear_cache()              │
                              │ + get_cache_stats()          │
                              └──────────────────────────────┘
```

## Flujo de Datos

### Escenario 1: Repositorio HTTP Simple

```
┌─────────┐         ┌──────────────────┐         ┌──────────────┐
│  Client │────────>│ HTTPJokeRepository│────────>│ JokeAPIClient│
│  Code   │         │                  │         │              │
└─────────┘         └──────────────────┘         └──────┬───────┘
                                                         │
                                                         ▼
                                                    ┌─────────┐
                                                    │ HTTP API│
                                                    └─────────┘

Flow:
1. Client calls: repo.get_joke_by_id(42)
2. HTTPJokeRepository delegates to JokeAPIClient
3. JokeAPIClient makes HTTP GET request
4. API returns JSON response
5. Response parsed into Joke object
6. Joke returned to client
```

### Escenario 2: Repositorio con Caché (Decorator Pattern)

```
┌─────────┐         ┌────────────────────┐         ┌──────────────────┐
│  Client │────────>│ CachedJokeRepository│───────>│ HTTPJokeRepository│
│  Code   │         │                    │         │                  │
└─────────┘         └─────────┬──────────┘         └────────┬─────────┘
                              │                              │
                              ▼                              ▼
                        ┌──────────┐                  ┌──────────────┐
                        │  Cache   │                  │ JokeAPIClient│
                        │  Memory  │                  └──────┬───────┘
                        └──────────┘                         │
                                                             ▼
                                                        ┌─────────┐
                                                        │ HTTP API│
                                                        └─────────┘

Flow (Cache HIT):
1. Client calls: repo.get_joke_by_id(42)
2. CachedJokeRepository checks cache
3. Cache entry found and not expired
4. Joke returned from cache (fast!)

Flow (Cache MISS):
1. Client calls: repo.get_joke_by_id(42)
2. CachedJokeRepository checks cache
3. Cache miss or expired
4. Delegates to wrapped HTTPJokeRepository
5. HTTPJokeRepository fetches from API
6. CachedJokeRepository stores in cache
7. Joke returned to client
```

## Patrón Factory

```
┌─────────────────────────────────────────────────────────┐
│               RepositoryFactory                         │
├─────────────────────────────────────────────────────────┤
│ + create_http_repository(**kwargs)                      │
│ + create_cached_repository(**kwargs)                    │
│ + create_repository(type, **kwargs)                     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ creates
                      ▼
     ┌────────────────┴──────────────────┐
     │                                   │
     ▼                                   ▼
┌──────────────┐              ┌──────────────────────┐
│ HTTP         │              │ Cached               │
│ Repository   │              │ Repository           │
└──────────────┘              └──────────────────────┘

Usage:
    repo = RepositoryFactory.create_repository("cached")
```

## Patrón Singleton

```
┌──────────────────────────────────────┐
│  get_joke_repository()               │
│  (Global Singleton Function)         │
└──────────┬───────────────────────────┘
           │
           ▼
    ┌─────────────┐
    │ _default_   │ <───────────┐
    │ repository  │             │
    └─────────────┘             │
           │                    │
           │ returns same       │ all calls
           │ instance           │ return same
           ▼                    │ object
    ┌─────────────┐             │
    │ Repository  │─────────────┘
    │ Instance    │
    └─────────────┘

First call:  Creates instance and stores it
Later calls: Returns stored instance
```

## Exception Hierarchy

```
Exception
    │
    └── JokeRepositoryError
            │
            ├── JokeNotFoundError
            │
            └── (future exceptions)

Mapping from API to Repository:
    JokeAPIError ──────────> JokeRepositoryError
    JokeAPIHTTPError(404) ─> JokeNotFoundError
    JokeAPIHTTPError(500) ─> JokeRepositoryError
    JokeAPITimeoutError ───> JokeRepositoryError
```

## Composición de Decoradores

El patrón Decorator permite apilar funcionalidad:

```
┌─────────────────────────────────────────────────────┐
│                  Client Code                        │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │ Logging Decorator     │  ─┐
            │ (logs all calls)      │   │
            └───────────┬───────────┘   │
                        │               │
                        ▼               │
            ┌───────────────────────┐   │
            │ Retry Decorator       │   │ Stack of
            │ (retry on failure)    │   │ decorators
            └───────────┬───────────┘   │ (composable)
                        │               │
                        ▼               │
            ┌───────────────────────┐   │
            │ Cache Decorator       │   │
            │ (caching layer)       │   │
            └───────────┬───────────┘   │
                        │               │
                        ▼              ─┘
            ┌───────────────────────┐
            │ HTTP Repository       │
            │ (base implementation) │
            └───────────────────────┘

Each decorator:
- Implements JokeRepository interface
- Wraps another JokeRepository
- Adds specific functionality
- Transparent to client
```

## Dependency Injection Pattern

```
┌───────────────────────────────────────────────┐
│          Application Layer                    │
│  (Services, Business Logic)                   │
└───────────────────┬───────────────────────────┘
                    │
                    │ depends on interface
                    │ (not implementation)
                    ▼
        ┌────────────────────────┐
        │  JokeRepository        │
        │  (Interface)           │
        └────────────────────────┘
                    ▲
                    │ implements
                    │
    ┌───────────────┴───────────────┐
    │                               │
    ▼                               ▼
┌─────────────┐           ┌──────────────────┐
│ HTTP Impl   │           │  Mock Impl       │
│ (Production)│           │  (Testing)       │
└─────────────┘           └──────────────────┘

Usage in code:
    def my_service(repository: JokeRepository):
        # Works with any implementation
        joke = repository.get_random_joke()

    # Production:
    my_service(HTTPJokeRepository())

    # Testing:
    my_service(MockJokeRepository())
```

## Cache Internal Structure

```
CachedJokeRepository
│
├── _cache: dict
│   ├── "joke:42" ──────> CacheEntry(value=Joke(...), expires_at=...)
│   ├── "joke:100" ─────> CacheEntry(value=Joke(...), expires_at=...)
│   └── "jokes:type:programming" ─> CacheEntry(value=Jokes(...), expires_at=...)
│
├── _stats: dict
│   ├── "hits" ──────> 42
│   ├── "misses" ────> 10
│   └── "evictions" ─> 3
│
└── _repository: JokeRepository
    └── (wrapped repository instance)

CacheEntry structure:
    ┌──────────────────┐
    │ value: Joke      │
    │ expires_at: dt   │
    └──────────────────┘
```

## Complete Request Flow Example

```
User Request: "Get joke ID 42"
│
▼
┌──────────────────────────────────────────────────────────┐
│ 1. Client Code                                            │
│    joke = repo.get_joke_by_id(42)                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 2. CachedJokeRepository.get_joke_by_id(42)               │
│    - Check cache for "joke:42"                           │
│    - If HIT: return cached value                         │
│    - If MISS: continue to step 3                         │
└────────────────────────┬─────────────────────────────────┘
                         │ cache miss
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 3. HTTPJokeRepository.get_joke_by_id(42)                 │
│    - Wrap in try/except                                  │
│    - Call JokeAPIClient                                  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 4. JokeAPIClient._make_request("/jokes/42", parser)      │
│    - Construct URL                                       │
│    - Make HTTP GET request                              │
│    - Handle errors                                       │
│    - Parse response                                      │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 5. External API                                          │
│    GET https://official-joke-api.appspot.com/jokes/42    │
│    Response: {"id": 42, "type": "...", ...}              │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│ 6. Response flows back up the chain                      │
│    API → JokeAPIClient → HTTPJokeRepository              │
│    → CachedJokeRepository (stores in cache)              │
│    → Client                                              │
└──────────────────────────────────────────────────────────┘
```

## Testing Strategy

```
┌────────────────────────────────────────────────────┐
│              Testing Pyramid                       │
│                                                    │
│                  /\                                │
│                 /  \  E2E Tests                    │
│                /────\  (Full stack)                │
│               /      \                             │
│              /        \ Integration Tests          │
│             /──────────\ (Repository + API)        │
│            /            \                          │
│           /              \ Unit Tests              │
│          /────────────────\ (Mock dependencies)    │
│         /                  \                       │
│        /____________________\                      │
│                                                    │
└────────────────────────────────────────────────────┘

Unit Tests:
    - Test each repository in isolation
    - Mock JokeAPIClient for HTTPJokeRepository
    - Test cache logic with MockRepository

Integration Tests:
    - Test repository with real JokeAPIClient
    - Verify error handling
    - Test cache behavior

E2E Tests:
    - Test entire application flow
    - Real API calls
    - Verify complete user scenarios
```

## Extension Points

```
Current:
    JokeRepository
        ├── HTTPJokeRepository
        └── CachedJokeRepository

Future Extensions:
    JokeRepository
        ├── HTTPJokeRepository
        ├── DatabaseJokeRepository  ─┐
        ├── FileJokeRepository      │ New
        ├── CompositeJokeRepository │ Implementations
        ├── CachedJokeRepository    ─┘
        ├── RetryJokeRepository     ─┐
        ├── LoggingJokeRepository   │ New
        ├── MetricsJokeRepository   │ Decorators
        └── CircuitBreakerRepository─┘
```

## Summary

**Patrones Implementados:**
1. ✅ Repository Pattern - Abstracción de datos
2. ✅ Decorator Pattern - Caché transparente
3. ✅ Factory Pattern - Creación centralizada
4. ✅ Singleton Pattern - Instancia global
5. ✅ Dependency Injection - Testabilidad

**Beneficios Clave:**
- 🎯 Desacoplamiento - Lógica separada de implementación
- 🧪 Testabilidad - Fácil uso de mocks
- 🔧 Extensibilidad - Agregar features sin romper código
- 📦 Composición - Decoradores apilables
- 🚀 Performance - Caché transparente

**Código Limpio:**
- SOLID principles
- Open/Closed principle (extensible sin modificar)
- Dependency Inversion (depende de abstracciones)
- Single Responsibility (cada clase una responsabilidad)
