"""
Pruebas unitarias para las herramientas registradas en main.py.

Se evita levantar el servidor MCP; solo se importan y ejecutan las
funciones decoradas como herramientas. Se sustituye el repositorio
global `joke_repo` por el `MockJokeRepository` definido en conftest.py
para evitar IO de red y tener datos deterministas.

Note: Environment variables (API_BASE_URL, LOCAL_TOKEN) are now managed
by the global ensure_env_vars fixture in conftest.py.
"""

import pytest


@pytest.fixture
def main_with_mock_repo(mock_repository):
    """
    Importa `main` y reemplaza el `joke_repo` global por el mock.
    Devuelve el módulo `main` listo para usar en pruebas.
    """
    # Importación tardía para asegurarnos de tener la variable de entorno lista
    import main as main_module

    # Reemplazar el repositorio por el mock provisto por conftest
    main_module.joke_repo = mock_repository
    return main_module


def test_tool_get_consistent_joke_returns_constant(main_with_mock_repo):
    from utils.constants import CONSISTENT_JOKE

    tool = main_with_mock_repo.tool_get_consistent_joke
    # Acceder a la función subyacente si fue envuelta por fastmcp
    # fastmcp.tools.tool.FunctionTool expone la función original en `.fn`
    result = tool.fn()
    assert result == CONSISTENT_JOKE


def test_tool_get_joke_uses_repository_and_formats(main_with_mock_repo):
    # Mock devuelve id=1 con "Setup 1" / "Punchline 1"
    tool = main_with_mock_repo.tool_get_joke
    result = tool.fn()
    assert result == "Setup 1\nPunchline 1"
    # Asegurar que el repositorio fue invocado
    assert main_with_mock_repo.joke_repo.calls["get_random_joke"] == 1


def test_tool_get_joke_by_id_valid_returns_formatted(main_with_mock_repo):
    tool = main_with_mock_repo.tool_get_joke_by_id
    result = tool.fn(2)
    assert result == "Setup 2\nPunchline 2"
    assert main_with_mock_repo.joke_repo.calls["get_joke_by_id"] == 1


def test_tool_get_joke_by_type_returns_first_formatted(main_with_mock_repo):
    # En el mock, solo id=2 es de tipo "programming"
    tool = main_with_mock_repo.tool_get_joke_by_type
    result = tool.fn("programming")
    assert result == "Setup 2\nPunchline 2"
    assert main_with_mock_repo.joke_repo.calls["get_jokes_by_type"] == 1
