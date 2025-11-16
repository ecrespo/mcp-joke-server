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
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(data)}\r\n\r\n".encode("ascii")
    fp.write(header)
    fp.write(data)
    fp.flush()


def _read_headers(fp) -> Optional[int]:
    """Lee cabeceras hasta línea en blanco y devuelve Content-Length.
    Ignora líneas que no contienen Content-Length.
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
    proc: Popen
    next_id: int = 1

    def request(self, method: str, params: Optional[JSON] = None) -> Tuple[int, JSON]:
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
    # Intentar usar uv si está disponible en PATH
    return ["uv", "run", "python", "main.py"]


def launch_server(cmd: str | None) -> Popen:
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
    return json.dumps(obj, ensure_ascii=False, indent=2)


def main(argv: Optional[List[str]] = None) -> int:
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
