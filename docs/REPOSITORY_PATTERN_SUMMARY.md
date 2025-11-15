# Implementación del Repository Pattern

## Resumen Ejecutivo

Se ha implementado el **Repository Pattern** para abstraer el acceso a datos de jokes, desacoplando la lógica de negocio de la fuente de datos específica. Esta implementación incluye múltiples patrones de diseño trabajando en conjunto para crear un sistema robusto, testeable y extensible.

## Patrones de Diseño Implementados

### 1. Repository Pattern
**Ubicación:** `repositories/base.py`

Define una interfaz abstracta para acceso a datos, proporcionando una capa de abstracción entre la lógica de negocio y la fuente de datos.

```python
class JokeRepository(ABC):
    @abstractmethod
    def get_random_joke(self) -> Joke:
        pass

    @abstractmethod
    def get_joke_by_id(self, joke_id: int) -> Joke:
        pass

    # ... más métodos
```

**Beneficios:**
- ✅ Desacopla lógica de negocio de implementación de datos
- ✅ Facilita testing con mocks
- ✅ Permite cambiar fuentes de datos sin modificar código cliente
- ✅ Centraliza lógica de acceso a datos

### 2. Decorator Pattern
**Ubicación:** `repositories/cached_repository.py`

Implementa un decorador que añade capacidades de caché a cualquier repositorio.

```python
class CachedJokeRepository(JokeRepository):
    def __init__(self, repository: JokeRepository, default_ttl: int = 300):
        self._repository = repository  # Envuelve cualquier repositorio
        self._cache = {}
```

**Beneficios:**
- ✅ Añade funcionalidad sin modificar código existente
- ✅ Composición sobre herencia
- ✅ Transparente para el cliente
- ✅ Puede apilar múltiples decoradores

### 3. Factory Pattern
**Ubicación:** `repositories/factory.py`

Centraliza la creación de repositorios con configuración apropiada.

```python
class RepositoryFactory:
    @staticmethod
    def create_repository(repository_type: RepositoryType, **kwargs) -> JokeRepository:
        # Lógica de creación centralizada
```

**Beneficios:**
- ✅ Centraliza lógica de creación
- ✅ Configuración basada en tipo
- ✅ Fácil de extender con nuevos tipos
- ✅ Oculta complejidad de construcción

### 4. Singleton Pattern
**Ubicación:** `repositories/factory.py` (función `get_joke_repository`)

Proporciona una única instancia del repositorio por defecto.

```python
_default_repository: JokeRepository | None = None

def get_joke_repository(force_recreate: bool = False, **kwargs) -> JokeRepository:
    global _default_repository
    if _default_repository is None or force_recreate:
        _default_repository = RepositoryFactory.create_repository(**kwargs)
    return _default_repository
```

**Beneficios:**
- ✅ Reutiliza conexiones/recursos
- ✅ Consistencia en toda la aplicación
- ✅ Reduce overhead de creación

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT CODE                              │
│              (main.py, tools, services)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              JokeRepository (Interface)                      │
│  • get_random_joke()                                        │
│  • get_joke_by_id()                                         │
│  • get_jokes_by_type()                                      │
│  • health_check()                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴────────────────┐
          │                                │
          ▼                                ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│ HTTPJokeRepository   │    │  CachedJokeRepository        │
│                      │    │  (Decorator)                 │
│ Uses:                │    │                              │
│ • JokeAPIClient      │    │  Wraps:                      │
│ • Direct HTTP calls  │    │  • Any JokeRepository        │
│                      │    │  • Adds caching layer        │
└──────────────────────┘    └──────────┬───────────────────┘
                                       │
                                       │ delegates to
                                       ▼
                          ┌──────────────────────┐
                          │  HTTPJokeRepository  │
                          │  (or other impl)     │
                          └──────────────────────┘
```

## Estructura de Archivos

```
repositories/
├── __init__.py                 # Exporta interfaces públicas
├── base.py                     # Interfaz abstracta + excepciones
├── http_repository.py          # Implementación HTTP
├── cached_repository.py        # Decorador de caché
└── factory.py                  # Factory + singleton

examples/
└── repository_pattern_demo.py  # Demostración de uso
```

## Componentes Detallados

### 1. Base Repository Interface (`base.py`)

#### `JokeRepository` (Abstract Base Class)
Define el contrato que deben cumplir todas las implementaciones:

- `get_random_joke()` - Obtiene un joke aleatorio
- `get_random_jokes(count)` - Obtiene múltiples jokes aleatorios
- `get_joke_by_id(joke_id)` - Obtiene un joke por ID
- `get_jokes_by_type(joke_type)` - Obtiene jokes por tipo
- `health_check()` - Verifica salud del repositorio

#### Excepciones Personalizadas

```python
JokeRepositoryError         # Error base del repositorio
JokeNotFoundError          # Joke no encontrado (404)
```

**Beneficios:**
- Jerarquía de excepciones clara
- Permite manejo granular de errores
- Desacopla excepciones de API de excepciones de repositorio

### 2. HTTP Repository (`http_repository.py`)

#### `HTTPJokeRepository`
Implementación concreta que obtiene datos de una API HTTP.

**Características:**
- Usa `JokeAPIClient` internamente
- Traduce excepciones de API a excepciones de repositorio
- Logging detallado de operaciones
- Manejo robusto de errores

**Ejemplo:**
```python
http_repo = HTTPJokeRepository()
joke = http_repo.get_joke_by_id(42)
```

**Traducción de Excepciones:**
```python
try:
    joke = self._client.get_joke_by_id(joke_id)
except JokeAPIHTTPError as e:
    if e.status_code == 404:
        raise JokeNotFoundError(joke_id)  # Excepción específica
    raise JokeRepositoryError("Failed to retrieve joke", cause=e)
```

### 3. Cached Repository (`cached_repository.py`)

#### `CachedJokeRepository`
Decorador que añade caché en memoria a cualquier repositorio.

**Características:**
- **TTL configurable** - Expiración automática de entradas
- **Cache selectivo** - No cachea jokes aleatorios
- **Estadísticas** - Hits, misses, hit rate, tamaño de caché
- **Auto-limpieza** - Elimina entradas expiradas
- **Transparente** - Misma interfaz que repositorio base

**Estrategia de Caché:**
```python
# No cachea (deben ser aleatorios)
get_random_joke()
get_random_jokes()

# Cachea con TTL largo (datos estáticos)
get_joke_by_id(42)     # TTL: 3600s (1 hora)

# Cachea con TTL medio (pueden cambiar)
get_jokes_by_type()    # TTL: 300s (5 minutos)
```

**Ejemplo de Uso:**
```python
# Envolver cualquier repositorio
base_repo = HTTPJokeRepository()
cached_repo = CachedJokeRepository(base_repo, default_ttl=300)

# Primera llamada - cache miss
joke1 = cached_repo.get_joke_by_id(42)  # Fetch de API

# Segunda llamada - cache hit
joke2 = cached_repo.get_joke_by_id(42)  # Desde caché

# Ver estadísticas
stats = cached_repo.get_cache_stats()
# {
#   'hits': 1,
#   'misses': 1,
#   'hit_rate_percent': 50.0,
#   'cache_size': 1
# }
```

**Implementación de Cache Entry:**
```python
class CacheEntry:
    def __init__(self, value, ttl_seconds):
        self.value = value
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
```

### 4. Repository Factory (`factory.py`)

#### `RepositoryFactory`
Factory class para crear repositorios configurados.

**Métodos:**
- `create_http_repository()` - Crea repositorio HTTP
- `create_cached_repository()` - Crea repositorio con caché
- `create_repository(type)` - Método principal factory

**Ejemplo:**
```python
# Crear diferentes tipos
http_repo = RepositoryFactory.create_repository("http")
cached_repo = RepositoryFactory.create_repository("cached", cache_ttl=600)
```

#### `get_joke_repository()` (Singleton)
Función de conveniencia que mantiene instancia singleton.

**Ejemplo:**
```python
# Primera llamada - crea instancia
repo1 = get_joke_repository()

# Segunda llamada - retorna misma instancia
repo2 = get_joke_repository()

assert repo1 is repo2  # True

# Forzar recreación
repo3 = get_joke_repository(force_recreate=True, repository_type="http")
```

## Casos de Uso

### Caso 1: Uso Básico (Recomendado)

```python
from repositories import get_joke_repository

# Obtener repositorio (cached por defecto)
repo = get_joke_repository()

# Usar normalmente
joke = repo.get_random_joke()
jokes = repo.get_jokes_by_type("programming")
specific_joke = repo.get_joke_by_id(42)
```

### Caso 2: Configuración Personalizada

```python
from repositories import RepositoryFactory

# Repositorio HTTP puro (sin caché)
http_repo = RepositoryFactory.create_repository(
    repository_type="http",
    timeout=15.0
)

# Repositorio con caché de 10 minutos
cached_repo = RepositoryFactory.create_repository(
    repository_type="cached",
    cache_ttl=600
)
```

### Caso 3: Testing con Mock Repository

```python
from repositories.base import JokeRepository
from utils.model import Joke

class MockJokeRepository(JokeRepository):
    """Mock repository para testing."""

    def get_joke_by_id(self, joke_id: int) -> Joke:
        return Joke(
            type="test",
            setup="Test setup",
            punchline="Test punchline",
            id=joke_id
        )

    # ... implementar otros métodos

# Usar en tests
def test_some_feature():
    mock_repo = MockJokeRepository()
    # Test usando mock en lugar de API real
```

### Caso 4: Múltiples Capas de Decoradores

```python
# Crear una cadena de decoradores
base_repo = HTTPJokeRepository()
cached_repo = CachedJokeRepository(base_repo)
# Podrías añadir más decoradores aquí
# logged_repo = LoggingRepository(cached_repo)
# retry_repo = RetryRepository(logged_repo)
```

## Beneficios de la Implementación

### 1. Abstracción y Desacoplamiento
```python
# El código cliente no sabe si usa HTTP, caché, DB, etc.
def get_programming_joke(repository: JokeRepository):
    jokes = repository.get_jokes_by_type("programming")
    return jokes.jokes[0]

# Funciona con cualquier implementación
http_joke = get_programming_joke(HTTPJokeRepository())
cached_joke = get_programming_joke(CachedJokeRepository(...))
mock_joke = get_programming_joke(MockJokeRepository())
```

### 2. Testing Simplificado
```python
# Antes (código acoplado a HTTP):
def test_get_joke():
    # Necesita servidor HTTP real o mocking complicado
    joke = get_joke_from_api()

# Después (con Repository Pattern):
def test_get_joke():
    mock_repo = MockJokeRepository()
    joke = mock_repo.get_joke_by_id(1)
    # Test simple, rápido, sin dependencias externas
```

### 3. Fácil Cambio de Fuente de Datos
```python
# Cambiar de HTTP a Base de Datos sin modificar código cliente
# Solo cambiar en un lugar:

# Antes:
repo = HTTPJokeRepository()

# Después:
repo = DatabaseJokeRepository()  # Misma interfaz

# El resto del código no cambia!
```

### 4. Composición Flexible
```python
# Composición de comportamientos con decoradores
repo = CachedJokeRepository(
    RetryJokeRepository(
        LoggingJokeRepository(
            HTTPJokeRepository()
        )
    )
)
```

## Comparación: Antes vs Después

### Antes (Sin Repository Pattern)
```python
# main.py - código acoplado
from utils.RequestAPIJokes import get_joke, get_joke_by_id

def my_function():
    joke = get_joke()  # Directamente acoplado a HTTP API
    # Si quiero caché, tengo que modificar get_joke()
    # Si quiero testing, necesito mockear httpx
```

**Problemas:**
- ❌ Acoplamiento directo a implementación HTTP
- ❌ Difícil de testear
- ❌ No se puede cambiar fuente de datos fácilmente
- ❌ No hay abstracción

### Después (Con Repository Pattern)
```python
# main.py - código desacoplado
from repositories import get_joke_repository

def my_function(repo: JokeRepository = None):
    repo = repo or get_joke_repository()  # Abstracción
    joke = repo.get_random_joke()
    # Caché incluido automáticamente
    # Testing fácil con MockRepository
```

**Ventajas:**
- ✅ Desacoplado de implementación
- ✅ Fácil de testear (inyección de dependencias)
- ✅ Cambio de fuente de datos trivial
- ✅ Abstracción clara

## Extensibilidad

### Agregar Nueva Fuente de Datos

Para agregar una nueva fuente de datos (ej: base de datos local):

```python
# repositories/database_repository.py
class DatabaseJokeRepository(JokeRepository):
    def __init__(self, db_connection):
        self._db = db_connection

    def get_joke_by_id(self, joke_id: int) -> Joke:
        row = self._db.query("SELECT * FROM jokes WHERE id = ?", joke_id)
        return Joke(**row)

    # ... implementar otros métodos
```

**Pasos:**
1. Crear clase que implemente `JokeRepository`
2. Implementar métodos abstractos
3. Agregar tipo a `RepositoryType` enum (opcional)
4. Actualizar factory (opcional)
5. ¡Listo! El código cliente no cambia

### Agregar Nuevo Decorador

Para agregar funcionalidad nueva (ej: retry logic):

```python
# repositories/retry_repository.py
class RetryJokeRepository(JokeRepository):
    def __init__(self, repository: JokeRepository, max_retries: int = 3):
        self._repository = repository
        self._max_retries = max_retries

    def get_joke_by_id(self, joke_id: int) -> Joke:
        for attempt in range(self._max_retries):
            try:
                return self._repository.get_joke_by_id(joke_id)
            except JokeRepositoryError:
                if attempt == self._max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
```

## Métricas y Observabilidad

### Cache Statistics
```python
cached_repo = CachedJokeRepository(...)

# Después de varias operaciones
stats = cached_repo.get_cache_stats()
print(f"Hit rate: {stats['hit_rate_percent']}%")
print(f"Cache size: {stats['cache_size']} entries")
print(f"Total requests: {stats['total_requests']}")
```

### Health Checks
```python
repo = get_joke_repository()

if not repo.health_check():
    # Alertar, fallback, etc.
    logger.error("Repository is unhealthy!")
```

## Mejores Prácticas

### 1. Usar Inyección de Dependencias
```python
# ✅ Bueno - permite testing
def process_jokes(repository: JokeRepository):
    return repository.get_random_joke()

# ❌ Malo - acoplado a implementación
def process_jokes():
    repo = HTTPJokeRepository()
    return repo.get_random_joke()
```

### 2. Usar el Singleton por Defecto
```python
# ✅ Bueno - reutiliza conexiones
repo = get_joke_repository()

# ⚠️ Menos ideal - crea nueva instancia cada vez
repo = RepositoryFactory.create_repository("cached")
```

### 3. Manejar Excepciones Específicas
```python
try:
    joke = repo.get_joke_by_id(999)
except JokeNotFoundError:
    # Manejar caso específico de "not found"
    joke = repo.get_random_joke()
except JokeRepositoryError as e:
    # Manejar otros errores de repositorio
    logger.error(f"Repository error: {e}")
```

## Testing

### Unit Test Ejemplo
```python
def test_cached_repository_caches_jokes():
    # Arrange
    mock_repo = MockJokeRepository()
    cached_repo = CachedJokeRepository(mock_repo)

    # Act
    joke1 = cached_repo.get_joke_by_id(1)
    joke2 = cached_repo.get_joke_by_id(1)

    # Assert
    assert joke1 is joke2  # Same object from cache
    stats = cached_repo.get_cache_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
```

## Próximos Pasos Sugeridos

1. **Añadir más implementaciones:**
   - `DatabaseJokeRepository` para persistencia local
   - `CompositeJokeRepository` para múltiples fuentes

2. **Añadir más decoradores:**
   - `RetryJokeRepository` con exponential backoff
   - `LoggingJokeRepository` para audit trail
   - `CircuitBreakerRepository` para resilencia

3. **Mejorar caché:**
   - Implementar LRU eviction policy
   - Soporte para Redis/Memcached
   - Cache warming strategies

4. **Observabilidad:**
   - Métricas con Prometheus
   - Distributed tracing
   - Logging estructurado

5. **Testing:**
   - Crear suite completa de unit tests
   - Integration tests con testcontainers
   - Property-based testing con Hypothesis

## Conclusión

La implementación del Repository Pattern proporciona:

✅ **Abstracción** - Código desacoplado de fuente de datos específica
✅ **Testabilidad** - Fácil de testear con mocks
✅ **Flexibilidad** - Fácil cambiar/agregar fuentes de datos
✅ **Composición** - Decoradores para añadir funcionalidad
✅ **Mantenibilidad** - Cambios localizados, bajo acoplamiento
✅ **Escalabilidad** - Base sólida para crecer

El sistema ahora está preparado para evolucionar sin romper código existente.
