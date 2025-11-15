# Guía de Migración al Repository Pattern

## Introducción

Esta guía ayuda a migrar código existente que usa directamente `utils.RequestAPIJokes` al nuevo sistema basado en Repository Pattern.

## Beneficios de Migrar

- ✅ **Testabilidad**: Fácil uso de mocks en tests
- ✅ **Caché**: Caché automático incluido
- ✅ **Flexibilidad**: Cambiar fuente de datos sin modificar código
- ✅ **Mantenibilidad**: Código más limpio y desacoplado
- ✅ **Observabilidad**: Estadísticas de caché, health checks

## Migración Paso a Paso

### Opción 1: Migración Simple (Recomendada)

Esta es la forma más rápida y simple de migrar.

#### Antes:
```python
from utils.RequestAPIJokes import (
    get_joke,
    get_joke_by_id,
    get_jokes_by_type,
    get_ten_jokes
)

# En tu código
joke = get_joke()
specific_joke = get_joke_by_id(42)
programming_jokes = get_jokes_by_type("programming")
many_jokes = get_ten_jokes()
```

#### Después:
```python
from repositories import get_joke_repository

# Obtener repositorio (una vez, al inicio)
repo = get_joke_repository()

# En tu código (cambiar llamadas)
joke = repo.get_random_joke()  # ← cambiado
specific_joke = repo.get_joke_by_id(42)  # ← sin cambios
programming_jokes = repo.get_jokes_by_type("programming")  # ← sin cambios
many_jokes = repo.get_random_jokes(10)  # ← cambiado
```

**Cambios necesarios:**
| Antes | Después |
|-------|---------|
| `get_joke()` | `repo.get_random_joke()` |
| `get_ten_jokes()` | `repo.get_random_jokes(10)` |
| `get_joke_by_id(id)` | `repo.get_joke_by_id(id)` |
| `get_jokes_by_type(type)` | `repo.get_jokes_by_type(type)` |

### Opción 2: Migración con Dependency Injection (Mejor para Testing)

Esta opción es mejor si quieres hacer tu código más testeable.

#### Antes:
```python
from utils.RequestAPIJokes import get_joke

def my_service_function():
    """Función de servicio que obtiene un joke."""
    joke = get_joke()
    return process_joke(joke)

def process_joke(joke):
    return f"{joke.setup} - {joke.punchline}"
```

#### Después:
```python
from repositories import get_joke_repository, JokeRepository

def my_service_function(repository: JokeRepository = None):
    """
    Función de servicio que obtiene un joke.

    Args:
        repository: Optional repository instance (for testing)
    """
    repo = repository or get_joke_repository()
    joke = repo.get_random_joke()
    return process_joke(joke)

def process_joke(joke):
    return f"{joke.setup} - {joke.punchline}"
```

**Beneficio**: Ahora puedes testear fácilmente:

```python
# test_my_service.py
from repositories.base import JokeRepository
from utils.model import Joke

class MockJokeRepository(JokeRepository):
    def get_random_joke(self):
        return Joke(
            type="test",
            setup="Why?",
            punchline="Because!",
            id=1
        )

def test_my_service_function():
    mock_repo = MockJokeRepository()
    result = my_service_function(repository=mock_repo)
    assert "Why?" in result
    assert "Because!" in result
```

### Opción 3: Migración de Clases

Si tienes clases que usan el API, migra de esta forma.

#### Antes:
```python
from utils.RequestAPIJokes import get_joke, get_joke_by_id

class JokeService:
    def __init__(self):
        pass

    def get_random(self):
        return get_joke()

    def get_by_id(self, joke_id: int):
        return get_joke_by_id(joke_id)
```

#### Después:
```python
from repositories import get_joke_repository, JokeRepository

class JokeService:
    def __init__(self, repository: JokeRepository = None):
        self._repository = repository or get_joke_repository()

    def get_random(self):
        return self._repository.get_random_joke()

    def get_by_id(self, joke_id: int):
        return self._repository.get_joke_by_id(joke_id)
```

**Ventajas:**
- Constructor acepta repositorio (dependency injection)
- Fácil de testear con mocks
- Puede usar diferentes implementaciones

## Manejo de Excepciones

Las excepciones también cambian. Actualiza tu manejo de errores.

### Antes:
```python
from utils.RequestAPIJokes import get_joke_by_id
from utils.exceptions import JokeAPIHTTPError, JokeAPITimeoutError

try:
    joke = get_joke_by_id(999)
except JokeAPIHTTPError as e:
    if e.status_code == 404:
        print("Joke not found")
    else:
        print(f"HTTP error: {e}")
except JokeAPITimeoutError:
    print("Timeout!")
```

### Después:
```python
from repositories import get_joke_repository
from repositories.base import JokeRepositoryError, JokeNotFoundError

repo = get_joke_repository()

try:
    joke = repo.get_joke_by_id(999)
except JokeNotFoundError as e:
    print(f"Joke not found: {e.joke_id}")
except JokeRepositoryError as e:
    print(f"Repository error: {e}")
    if e.cause:
        print(f"Caused by: {e.cause}")
```

**Beneficios:**
- Excepciones más específicas (`JokeNotFoundError`)
- Desacoplado de detalles HTTP
- Acceso a causa original si necesario

## Configuración

### Usando Configuración por Defecto (Recomendado)

```python
from repositories import get_joke_repository

# Obtiene repositorio cached por defecto
repo = get_joke_repository()
```

### Configuración Personalizada

```python
from repositories import RepositoryFactory

# Solo HTTP (sin caché)
http_repo = RepositoryFactory.create_repository("http", timeout=15.0)

# Con caché personalizado
cached_repo = RepositoryFactory.create_repository(
    "cached",
    cache_ttl=600  # 10 minutos
)

# Forzar recreación
repo = get_joke_repository(
    force_recreate=True,
    repository_type="http"
)
```

## Ejemplos de Migración Completos

### Ejemplo 1: Script Simple

#### Antes:
```python
#!/usr/bin/env python3
from utils.RequestAPIJokes import get_joke

def main():
    joke = get_joke()
    print(f"{joke.setup}")
    print(f"{joke.punchline}")

if __name__ == "__main__":
    main()
```

#### Después:
```python
#!/usr/bin/env python3
from repositories import get_joke_repository

def main():
    repo = get_joke_repository()
    joke = repo.get_random_joke()
    print(f"{joke.setup}")
    print(f"{joke.punchline}")

if __name__ == "__main__":
    main()
```

### Ejemplo 2: Servicio con Múltiples Operaciones

#### Antes:
```python
from utils.RequestAPIJokes import (
    get_joke,
    get_joke_by_id,
    get_jokes_by_type
)

class JokeManager:
    def get_random_programming_joke(self):
        jokes = get_jokes_by_type("programming")
        if jokes.jokes:
            return jokes.jokes[0]
        return None

    def get_favorite_joke(self):
        return get_joke_by_id(42)

    def get_any_joke(self):
        return get_joke()
```

#### Después:
```python
from repositories import get_joke_repository, JokeRepository

class JokeManager:
    def __init__(self, repository: JokeRepository = None):
        self._repo = repository or get_joke_repository()

    def get_random_programming_joke(self):
        jokes = self._repo.get_jokes_by_type("programming")
        if jokes.jokes:
            return jokes.jokes[0]
        return None

    def get_favorite_joke(self):
        return self._repo.get_joke_by_id(42)

    def get_any_joke(self):
        return self._repo.get_random_joke()
```

### Ejemplo 3: Con Tests

#### Antes (difícil de testear):
```python
# service.py
from utils.RequestAPIJokes import get_joke

def format_joke_for_display():
    joke = get_joke()  # Llamada HTTP directa
    return f"[{joke.type.upper()}] {joke.setup} → {joke.punchline}"

# test_service.py (complicado, necesita mockear httpx)
import httpx
from unittest.mock import patch

def test_format_joke():
    with patch('httpx.get') as mock_get:
        # Configurar mock complicado...
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'type': 'test',
            'setup': 'Why?',
            'punchline': 'Because',
            'id': 1
        }
        result = format_joke_for_display()
        assert 'TEST' in result
```

#### Después (fácil de testear):
```python
# service.py
from repositories import get_joke_repository, JokeRepository

def format_joke_for_display(repository: JokeRepository = None):
    repo = repository or get_joke_repository()
    joke = repo.get_random_joke()
    return f"[{joke.type.upper()}] {joke.setup} → {joke.punchline}"

# test_service.py (simple y limpio)
from repositories.base import JokeRepository
from utils.model import Joke

class MockJokeRepository(JokeRepository):
    def get_random_joke(self):
        return Joke(type='test', setup='Why?', punchline='Because', id=1)

    # Otros métodos pueden levantar NotImplementedError
    def get_joke_by_id(self, joke_id):
        raise NotImplementedError()

    def get_jokes_by_type(self, joke_type):
        raise NotImplementedError()

    def get_random_jokes(self, count):
        raise NotImplementedError()

    def health_check(self):
        return True

def test_format_joke():
    mock_repo = MockJokeRepository()
    result = format_joke_for_display(repository=mock_repo)
    assert 'TEST' in result
    assert 'Why?' in result
```

## Características Adicionales

### 1. Cache Statistics

```python
from repositories import get_joke_repository, CachedJokeRepository

repo = get_joke_repository()

# Usar el repositorio...
joke1 = repo.get_joke_by_id(42)
joke2 = repo.get_joke_by_id(42)  # Cache hit!

# Ver estadísticas (si es cached)
if isinstance(repo, CachedJokeRepository):
    stats = repo.get_cache_stats()
    print(f"Hit rate: {stats['hit_rate_percent']}%")
    print(f"Cache size: {stats['cache_size']}")
```

### 2. Health Checks

```python
from repositories import get_joke_repository

repo = get_joke_repository()

if not repo.health_check():
    print("⚠️ Repository is unhealthy!")
    # Implementar fallback, alertas, etc.
else:
    print("✓ Repository is healthy")
```

### 3. Clear Cache

```python
from repositories import get_joke_repository, CachedJokeRepository

repo = get_joke_repository()

if isinstance(repo, CachedJokeRepository):
    # Limpiar caché si necesario
    repo.clear_cache()
    print("Cache cleared")
```

## Checklist de Migración

- [ ] Identificar todos los imports de `utils.RequestAPIJokes`
- [ ] Reemplazar con `from repositories import get_joke_repository`
- [ ] Cambiar llamadas a funciones:
  - [ ] `get_joke()` → `repo.get_random_joke()`
  - [ ] `get_ten_jokes()` → `repo.get_random_jokes(10)`
  - [ ] `get_joke_by_id()` → `repo.get_joke_by_id()`
  - [ ] `get_jokes_by_type()` → `repo.get_jokes_by_type()`
- [ ] Actualizar manejo de excepciones:
  - [ ] Importar `JokeRepositoryError`, `JokeNotFoundError`
  - [ ] Actualizar bloques try/except
- [ ] Agregar dependency injection donde sea apropiado
- [ ] Actualizar tests para usar mocks de repositorio
- [ ] Verificar que todo funcione
- [ ] Aprovechar nuevas features (cache stats, health checks)

## Troubleshooting

### Problema: "JokeRepository object has no attribute X"

**Causa**: Intentando llamar método que no existe.

**Solución**: Verificar nombres de métodos:
- ❌ `repo.get_joke()`
- ✅ `repo.get_random_joke()`

### Problema: Cache no funciona

**Causa**: Usando HTTPJokeRepository en lugar de CachedJokeRepository.

**Solución**:
```python
# Asegurar que obtienes repositorio cached
repo = get_joke_repository()  # Default es cached

# O explícitamente
from repositories import RepositoryFactory
repo = RepositoryFactory.create_repository("cached")
```

### Problema: Tests fallan con "module 'loguru' not found"

**Causa**: Dependencias no instaladas.

**Solución**:
```bash
uv sync  # o pip install -r requirements.txt
```

### Problema: "TypeError: metaclass conflict"

**Causa**: Problema con metaclasses (ya resuelto en la implementación).

**Solución**: Asegurar que estás usando la versión correcta de `config.py`.

## Migración Gradual

No necesitas migrar todo de una vez. Puedes:

1. **Fase 1**: Agregar repositorios en código nuevo
2. **Fase 2**: Migrar código existente módulo por módulo
3. **Fase 3**: Deprecar funciones antiguas (opcional)

**Compatibilidad**: Las funciones antiguas (`get_joke()`, etc.) aún existen y funcionan. Puedes migrar gradualmente.

## Próximos Pasos Después de Migrar

1. **Aprovechar el caché**
   - Configurar TTL apropiado
   - Monitorear hit rate

2. **Mejorar tests**
   - Usar mocks de repositorio
   - Tests más rápidos y confiables

3. **Agregar observabilidad**
   - Health checks periódicos
   - Métricas de caché
   - Logging mejorado

4. **Considerar extensiones**
   - Repositorio de base de datos local
   - Decorador de retry
   - Circuit breaker

## Resumen

| Aspecto | Antes | Después |
|---------|-------|---------|
| Import | `from utils.RequestAPIJokes import get_joke` | `from repositories import get_joke_repository` |
| Uso | `joke = get_joke()` | `repo = get_joke_repository()`<br>`joke = repo.get_random_joke()` |
| Testing | Mock de httpx (complicado) | Mock de Repository (simple) |
| Caché | No incluido | Incluido por defecto |
| Flexibilidad | Acoplado a HTTP | Abstracción, fácil cambiar |
| Excepciones | Excepciones de API | Excepciones de Repository |

La migración mejora significativamente la calidad del código y facilita el mantenimiento futuro.
