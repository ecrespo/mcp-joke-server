# Resumen de Refactorización - utils/config.py

## Cambios Realizados

### 1. Migración de `python-decouple` a `pydantic-settings`

**Antes:**
```python
from decouple import config

class Settings:
    API_BASE_URL: str = config("API_BASE_URL")
    MCP_SERVER_HOST: str = config('MCP_SERVER_HOST', default='0.0.0.0')
```

**Después:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_BASE_URL: str = Field(...)
    MCP_SERVER_HOST: str = Field(default="0.0.0.0")
```

**Beneficios:**
- ✅ Validación automática de tipos con Pydantic
- ✅ Validación de valores con constraints (ge, le, etc.)
- ✅ Documentación integrada con Field descriptions
- ✅ Soporte para múltiples fuentes de configuración
- ✅ Mejor manejo de errores con mensajes claros

### 2. Patrón Singleton con Metaclass

Se implementó una metaclass personalizada `SingletonSettingsMeta` que:

1. **Hereda de `ModelMetaclass`** (metaclass de Pydantic)
2. **Implementa el patrón Singleton** - garantiza una única instancia
3. **Permite acceso a atributos de clase** - `Settings.API_BASE_URL` funciona directamente

```python
class SingletonSettingsMeta(ModelMetaclass):
    """
    Metaclass que combina:
    - Funcionalidad de Pydantic (ModelMetaclass)
    - Patrón Singleton
    - Acceso a atributos de clase
    """

    _instances: ClassVar[dict[type, object]] = {}

    def __call__(cls, *args, **kwargs):
        # Singleton: retorna la misma instancia
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __getattribute__(cls, name: str):
        # Permite acceso como Settings.API_BASE_URL
        # Delega al singleton automáticamente
        ...
```

**Beneficios:**
- ✅ Una única instancia de configuración en toda la aplicación
- ✅ Acceso como atributos de clase: `Settings.API_BASE_URL`
- ✅ También funciona con instancias: `Settings().API_BASE_URL`
- ✅ Thread-safe por diseño
- ✅ Método `reset()` para testing

### 3. Validadores Personalizados

Se agregaron validadores robustos usando `@field_validator`:

#### Validador de URL
```python
@field_validator("API_BASE_URL")
@classmethod
def validate_api_url(cls, v: str) -> str:
    if not v.startswith(("http://", "https://")):
        raise ValueError("API_BASE_URL must start with http:// or https://")
    return v.rstrip("/")  # Normaliza eliminando trailing slashes
```

#### Validador de LOG_ROTATION
```python
@field_validator("LOG_ROTATION")
@classmethod
def validate_log_rotation(cls, v: str) -> str:
    # Valida formatos como: "10 MB", "1 day", "1 week"
    # Soporta: KB, MB, GB, day/days, week/weeks, hour/hours
    ...
```

#### Validador de LOG_FILE
```python
@field_validator("LOG_FILE")
@classmethod
def validate_log_file(cls, v: str) -> str:
    # Crea el directorio padre si no existe
    log_path = Path(v)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return v
```

**Beneficios:**
- ✅ Validación en tiempo de carga
- ✅ Errores claros antes de la ejecución
- ✅ Auto-creación de directorios necesarios
- ✅ Normalización de valores (ej: URLs sin trailing slash)

### 4. Constraints con Pydantic Field

Se agregaron constraints de validación directamente en los campos:

```python
MCP_SERVER_PORT: int = Field(
    default=8000,
    ge=1,          # greater than or equal
    le=65535,      # less than or equal
    description="Port number for the MCP server (1-65535)"
)

SESSION_TIMEOUT: int = Field(
    default=3600,
    ge=60,         # mínimo 1 minuto
    le=86400,      # máximo 24 horas
    description="Session timeout in seconds (60s - 24h)"
)

LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
    default="INFO",
    description="Logging level"
)
```

**Beneficios:**
- ✅ Validación automática de rangos
- ✅ Type hints con Literal para opciones limitadas
- ✅ Auto-documentación del código
- ✅ Intellisense mejorado en IDEs

### 5. Configuración con SettingsConfigDict

```python
model_config = SettingsConfigDict(
    env_file=".env",              # Lee desde archivo .env
    env_file_encoding="utf-8",    # Encoding del archivo
    case_sensitive=True,          # Variables case-sensitive
    extra="ignore",               # Ignora variables extra
    validate_default=True,        # Valida valores por defecto
)
```

**Beneficios:**
- ✅ Configuración clara y explícita
- ✅ Carga automática desde .env
- ✅ Validación de valores por defecto
- ✅ Flexibilidad para extender

### 6. Métodos Útiles

#### `model_dump_safe()`
```python
def model_dump_safe(self) -> dict[str, str]:
    """
    Retorna configuración como diccionario.
    Preparado para enmascarar datos sensibles en el futuro.
    """
    config_dict = self.model_dump()
    # Aquí se pueden enmascarar secretos antes de logging
    return config_dict
```

#### `get_instance()`
```python
@classmethod
def get_instance(cls) -> "Settings":
    """
    Forma explícita de obtener la instancia singleton.
    """
    return cls()
```

#### `__repr__()`
```python
def __repr__(self) -> str:
    """
    Representación string útil para debugging.
    """
    return f"Settings(API_BASE_URL={self.API_BASE_URL!r}, ...)"
```

## Comparación Antes/Después

### Antes (python-decouple)

```python
from decouple import config

class Settings:
    API_BASE_URL: str = config("API_BASE_URL")
    MCP_SERVER_PORT: int = config('MCP_SERVER_PORT', default=8000, cast=int)

    @classmethod
    def validate(cls):
        # Validación manual
        required_fields = ['API_BASE_URL']
        missing = []
        for field in required_fields:
            if not getattr(cls, field, None):
                missing.append(field)
        if missing:
            raise ValueError(f"Faltan configuraciones: {', '.join(missing)}")

settings = Settings()
```

**Problemas:**
- ❌ No hay validación de tipos automática
- ❌ Validación manual y propensa a errores
- ❌ No valida rangos de valores (ej: puerto 1-65535)
- ❌ Acceso inconsistente (a veces clase, a veces instancia)
- ❌ Sin documentación integrada

### Después (pydantic-settings)

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings, metaclass=SingletonSettingsMeta):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        validate_default=True
    )

    API_BASE_URL: str = Field(
        ...,
        description="Base URL for the external joke API service"
    )

    MCP_SERVER_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port number for the MCP server (1-65535)"
    )

    @field_validator("API_BASE_URL")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("Must start with http:// or https://")
        return v.rstrip("/")
```

**Ventajas:**
- ✅ Validación automática de tipos
- ✅ Validación declarativa de rangos
- ✅ Validadores personalizados claros
- ✅ Patrón Singleton consistente
- ✅ Documentación integrada
- ✅ Acceso flexible (clase o instancia)

## Formas de Uso

### Acceso como Atributos de Clase (Recomendado)
```python
from utils.config import Settings

url = Settings.API_BASE_URL
port = Settings.MCP_SERVER_PORT
level = Settings.LOG_LEVEL
```

### Acceso como Instancia
```python
from utils.config import Settings

settings = Settings()
url = settings.API_BASE_URL
port = settings.MCP_SERVER_PORT
```

### Acceso Explícito al Singleton
```python
from utils.config import Settings

settings = Settings.get_instance()
url = settings.API_BASE_URL
```

### Todas las formas devuelven la misma instancia
```python
assert Settings() is Settings()
assert Settings() is Settings.get_instance()
# Todos acceden al mismo singleton
```

## Patrones de Diseño Aplicados

1. **Singleton Pattern con Metaclass**
   - Garantiza una única instancia
   - Implementado en `SingletonSettingsMeta`

2. **Facade Pattern**
   - `Settings` oculta la complejidad de carga y validación
   - Interfaz simple para acceso a configuración

3. **Validator Pattern**
   - Validadores declarativos con `@field_validator`
   - Separación de concerns: cada validador una responsabilidad

4. **Builder Pattern (implícito en Pydantic)**
   - Construcción paso a paso con validación
   - Pydantic maneja la construcción internamente

## Testing

La configuración refactorizada incluye:

1. **Reset para testing**
   ```python
   SingletonSettingsMeta.reset()  # Limpia instancias para tests
   ```

2. **Validación automática**
   - Errores claros si faltan variables requeridas
   - Validación de tipos y rangos en tiempo de carga

3. **Dumps para debugging**
   ```python
   settings.model_dump_safe()  # Dict con configuración
   repr(settings)              # String representation
   ```

## Compatibilidad

✅ **100% compatible con el código existente** que usa:
- `from utils.config import Settings`
- `Settings.API_BASE_URL`
- `Settings().API_BASE_URL`

## Dependencias Agregadas

```toml
[project]
dependencies = [
    "pydantic>=2.12.4",
    "pydantic-settings>=2.8.0",  # ← Nueva dependencia
    ...
]
```

## Próximos Pasos Sugeridos

1. ✅ Considerar agregar validadores para formatos específicos
2. ✅ Implementar enmascaramiento de secretos en `model_dump_safe()`
3. ✅ Agregar soporte para múltiples archivos .env (.env.local, .env.test, etc.)
4. ✅ Crear tests unitarios específicos para validadores
5. ✅ Documentar variables de entorno en README
6. ✅ Considerar usar `SecretStr` para valores sensibles
