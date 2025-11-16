"""
Cliente mínimo para interactuar con el servidor MCP (fastmcp) por stdio.

Este script:
  1) Lanza el servidor `main.py` como subproceso (por defecto con `uv run python main.py`).
  2) Implementa el framing `Content-Length` y JSON-RPC 2.0 del protocolo MCP.
  3) Envía `initialize` → `tools/list` → `tools/call` a una o más herramientas.

Uso rápido (en dos terminales):
  Terminal A (opcional si prefieres lanzarlo tú):
    uv run python main.py

  Terminal B (este cliente; por defecto lanzará el servidor él mismo):
    python examples/mcp_client.py

  Opciones:
    - Para forzar el comando del servidor: 
        python examples/mcp_client.py --server-cmd "uv run python main.py"
    - Para llamar a una herramienta específica (por nombre):
        python examples/mcp_client.py --tool tool_get_consistent_joke
    - Para pasar argumentos JSON a la herramienta:
        python examples/mcp_client.py --tool tool_get_joke_by_id --args '{"joke_id": 2}'

Notas:
- Asegúrate de tener `API_BASE_URL` configurado (por .env o variables de entorno), p.ej.:
    API_BASE_URL=https://official-joke-api.appspot.com
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from dataclasses import dataclass
from subprocess import Popen, PIPE
from typing import Any, Dict, List, Optional, Tuple


JSON = Dict[str, Any]


def _write_message(fp, obj: JSON) -> None:
    """
    Serialize an object into a JSON-encoded message and write it
    to the specified file-like object with a Content-Length header.

    :param fp: A file-like object implementing write and flush methods,
               used for writing the serialized JSON message and header.
    :type fp: Any

    :param obj: The JSON-serializable object to be serialized into a
                JSON message and written to the file-like object.
    :type obj: JSON

    :return: None
    """
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    fp.write(header)
    fp.write(data)
    fp.flush()


def _read_headers(fp) -> Optional[int]:
    """
    Reads HTTP headers from a provided file-like object until a double newline
    sequence (\r\n\r\n) or its equivalent (\n) is encountered. If a Content-Length
    header is present, its value will be extracted and returned as an integer. The
    function supports decoding header lines using ASCII, skipping inconsistencies
    or errors, and ignoring other headers that are not relevant.

    :param fp: File-like object to read the HTTP headers from. Must support
               `readline()` method returning bytes.
    :return: The extracted integer value from the Content-Length header, or None
             if the Content-Length header is not found or headers cannot be read.
    :rtype: Optional[int]
    """
    content_length: Optional[int] = None
    # Leer líneas hasta \r\n\r\n
    # Algunas implementaciones pueden emitir saltos de línea estilo "\n".
    # Usamos un bucle que corta al encontrar una línea vacía.
    while True:
        line = fp.readline()
        if not line:
            return None  # EOF
        # Normalizar
        try:
            s = line.decode("ascii", errors="ignore").strip()
        except Exception:
            s = ""
        if s == "":
            break
        low = s.lower()
        if low.startswith("content-length:"):
            try:
                content_length = int(s.split(":", 1)[1].strip())
            except Exception:
                pass
        # Otras cabeceras se ignoran
    return content_length


def _read_message(fp) -> Optional[JSON]:
    """
    Reads a JSON message from a file-like object.

    The function attempts to read a structured JSON message from the provided
    file-like object by first determining its length and subsequently parsing
    the payload as a JSON document. It handles decoding errors by attempting
    to find the first valid JSON structure in the raw data, and if none exists,
    it falls back to returning a dictionary with the raw data for further inspection.

    :param fp: A file-like object from which the JSON message is to be read.
    :type fp: file-like object
    :return: The parsed JSON data if successful, `None` if no data exists,
             or a dictionary with raw data if the JSON decoding fails.
    :rtype: Optional[dict]
    """
    length = _read_headers(fp)
    if length is None:
        return None
    if length == 0:
        return {}
    data = fp.read(length)
    if not data:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        # Si hubiera logs mezclados en stdout, podemos intentar encontrar el primer '{'
        text = data.decode("utf-8", errors="ignore")
        idx = text.find("{")
        if idx != -1:
            try:
                return json.loads(text[idx:])
            except Exception:
                pass
        return {"_raw": text}


@dataclass
class RpcClient:
    """
    Represents a JSON-RPC client capable of sending requests to and receiving responses from
    a subprocess.

    This class is designed to provide an interface for interaction with a subprocess using
    JSON-RPC protocol. It supports sending requests to the process and reading responses
    associated with a specific request ID.

    :ivar proc: The subprocess to which this client sends requests and reads responses from.
    :type proc: Popen
    :ivar next_id: The sequential identifier used for each JSON-RPC request.
    :type next_id: int
    """
    proc: Popen
    next_id: int = 1

    def request(self, method: str, params: Optional[JSON] = None) -> Tuple[int, JSON]:
        """
        Sends a JSON-RPC 2.0 request message to the process' stdin.

        The method constructs a JSON-RPC 2.0 formatted request message with a given
        method name and optional parameters. It then sends the message to the
        process' standard input stream. Each request message includes a unique ID
        which is automatically incremented for each call. The function returns
        both the ID and the constructed message for further use.

        :param method: The name of the procedure or operation to invoke.
        :type method: str
        :param params: An optional dictionary containing the parameters for the
            requested method. If not provided, an empty dictionary is used instead.
        :type params: Optional[JSON]
        :return: A tuple containing the unique request ID and the JSON-RPC 2.0
            formatted request message as a dictionary.
        :rtype: Tuple[int, JSON]
        """
        rid = self.next_id
        self.next_id += 1
        msg: JSON = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": method,
            "params": params or {},
        }
        _write_message(self.proc.stdin, msg)
        return rid, msg

    def read_until_response(self, rid: int, timeout: float = 10.0) -> JSON:
        """
        Reads responses until a specific response with the given `rid` is matched or
        the timeout is reached.

        This function continuously reads data from the process output stream and checks
        for the presence of a specific response message with the provided request ID
        (`rid`). If the message with the matching request ID is not found within the
        timeout duration, a TimeoutError is raised. If the response contains an error
        field, a RuntimeError is raised.

        :param rid: The request ID to look for in the response.
        :param timeout: The maximum time in seconds to wait for the response. Defaults
            to 10.0 seconds.
        :return: The JSON object of the matched response containing the specified
            request ID.
        :raises TimeoutError: If the specified timeout duration is exceeded without
            receiving a response with the matching request ID.
        :raises RuntimeError: If the response contains an error field.
        """
        start = time.time()
        while True:
            if time.time() - start > timeout:
                raise TimeoutError(f"Timeout esperando respuesta a id={rid}")
            obj = _read_message(self.proc.stdout)
            if obj is None:
                # Dormir breve para no ocupar CPU si no hay datos
                time.sleep(0.01)
                continue
            # Filtrar notificaciones (sin id)
            if isinstance(obj, dict) and obj.get("id") == rid:
                if "error" in obj:
                    raise RuntimeError(f"RPC error: {obj['error']}")
                return obj


def _default_server_cmd() -> List[str]:
    """
    Generates the default command for running the server. The implementation checks
    if `uv` is available in the system's PATH and uses it to construct the command.

    :return: List of strings representing the default server command.
    :rtype: List[str]
    """
    # Intentar usar uv si está disponible en PATH
    return ["uv", "run", "python", "main.py"]


def launch_server(cmd: str | None) -> Popen:
    """
    Launches a server process using the provided command or a default command.

    If a command is specified, the method parses the command using `shlex.split`
    to create arguments for the process. If a command is not provided, a default
    server command is used instead. In case the specified executable cannot be
    found, this method falls back to launching a Python script named `main.py`.
    The method ensures that the process has valid `stdin` and `stdout` streams.

    :param cmd: The command to launch the server process. If None, a default
        server command will be used.
    :type cmd: str | None

    :return: A `Popen` object representing the launched server process.
    :rtype: Popen
    """
    if cmd:
        args = shlex.split(cmd)
    else:
        args = _default_server_cmd()
    try:
        proc = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    except FileNotFoundError:
        # fallback a python directo
        proc = Popen([sys.executable, "main.py"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    assert proc.stdin and proc.stdout
    return proc


def pretty(obj: Any) -> str:
    """
    Formats a given Python object as a JSON string with indentation.

    This function takes a Python object and serializes it to a JSON-formatted
    string. The output JSON will be indented with 2 spaces, and non-ASCII
    characters will stay in their original form instead of being escaped.

    :param obj: The Python object to serialize to JSON.
    :type obj: Any
    :return: A JSON-formatted string representing the input Python object.
    :rtype: str
    """
    return json.dumps(obj, ensure_ascii=False, indent=2)


def main(argv: Optional[List[str]] = None) -> int:
    """
    Runs the MCP client for fastmcp over standard IO.

    This script initializes a connection with the MCP server, lists available tools,
    and invokes a specified tool with provided arguments. It also displays results
    in a human-readable format and ensures a clean shutdown of the server.

    :param argv: List of command-line arguments. Defaults to None.
    :type argv: Optional[List[str]]

    :return: Exit status code. Returns 0 on success, 2 on JSON decoding error or
        other operational failure.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description="Cliente MCP por stdio para fastmcp")
    parser.add_argument(
        "--server-cmd",
        help="Comando para lanzar el servidor (default: 'uv run python main.py')",
    )
    parser.add_argument(
        "--tool",
        help="Nombre de la herramienta a llamar (default: tool_get_consistent_joke)",
        default="tool_get_consistent_joke",
    )
    parser.add_argument(
        "--args",
        help="JSON con argumentos para la herramienta (p.ej. '{\"joke_id\": 2}')",
        default="{}",
    )
    args = parser.parse_args(argv)

    # Lanzar servidor
    proc = launch_server(args.server_cmd)
    client = RpcClient(proc)

    # 1) initialize
    init_params: JSON = {
        "capabilities": {
            "experimental": {},
        },
        # Algunos servidores esperan un clienteId / nombre
        "clientInfo": {"name": "examples/mcp_client.py", "version": "0.1.0"},
    }
    rid, _ = client.request("initialize", init_params)
    init_resp = client.read_until_response(rid)
    print("Initialize result:\n" + pretty(init_resp.get("result")))

    # 2) tools/list
    rid, _ = client.request("tools/list", {})
    tools_resp = client.read_until_response(rid)
    tools = tools_resp.get("result", {}).get("tools", [])
    print("\nTools disponibles:")
    for t in tools:
        print(f"- {t.get('name')} : {t.get('description','')}")

    # 3) tools/call
    try:
        tool_args = json.loads(args.args)
    except json.JSONDecodeError:
        print("--args no es JSON válido", file=sys.stderr)
        return 2

    call_params = {
        "name": args.tool,
        "arguments": tool_args,
    }
    rid, _ = client.request("tools/call", call_params)
    call_resp = client.read_until_response(rid)
    result = call_resp.get("result", {})
    print("\nResultado tools/call:\n" + pretty(result))

    # Intenta extraer texto si está presente en formato MCP (content blocks)
    content = result.get("content")
    if isinstance(content, list) and content:
        texts = [c.get("text") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        if texts:
            print("\nTexto devuelto:\n" + "\n".join(texts))

    # Cierre ordenado
    try:
        # Algunos servidores aceptan shutdown/exit; si no, se matará al GC
        rid, _ = client.request("shutdown", {})
        _ = client.read_until_response(rid, timeout=2.0)
    except Exception:
        pass
    finally:
        proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
