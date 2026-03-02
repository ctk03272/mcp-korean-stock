from __future__ import annotations

import json
import sys

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.tools import ToolRegistry


def run_stdio_server(registry: ToolRegistry) -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = _handle_request(registry, request)
        except KoreanStockMcpError as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": exc.to_dict()}
        except Exception as exc:  # pragma: no cover
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": "INTERNAL_ERROR", "message": str(exc)}}
        sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
        sys.stdout.flush()


def _handle_request(registry: ToolRegistry, request: dict) -> dict:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": registry.list_tools()}}
    if method == "tools/call":
        result = registry.call_tool(params["name"], params.get("arguments"))
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"ok": True}}
    raise KoreanStockMcpError("METHOD_NOT_FOUND", f"Unsupported method '{method}'.")
