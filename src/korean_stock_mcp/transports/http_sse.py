from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.tools import ToolRegistry
from korean_stock_mcp.transports.stdio import _handle_request


def run_http_server(registry: ToolRegistry, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                self._send_json(HTTPStatus.OK, {"ok": True, "transport": "http"})
                return
            if self.path == "/sse":
                body = b"event: ready\ndata: {\"ok\":true}\n\n"
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/tools":
                self._send_json(HTTPStatus.OK, {"tools": registry.list_tools()})
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/mcp":
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length)
            try:
                request = json.loads(raw_body)
                response = _handle_request(registry, request)
                self._send_json(HTTPStatus.OK, response)
            except KoreanStockMcpError as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"jsonrpc": "2.0", "id": None, "error": exc.to_dict()})
            except Exception as exc:  # pragma: no cover
                self._send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"jsonrpc": "2.0", "id": None, "error": {"code": "INTERNAL_ERROR", "message": str(exc)}},
                )

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((host, port), Handler)
    server.serve_forever()
