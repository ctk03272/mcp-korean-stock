from __future__ import annotations

from collections.abc import Callable

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.services import MarketDataService


class ToolRegistry:
    def __init__(self, service: MarketDataService) -> None:
        self.service = service
        self._tools: dict[str, tuple[Callable[..., dict], dict]] = {
            "search_korean_stocks": (
                self.service.search_stocks,
                {
                    "description": "Search Korean stocks by 6-digit code or company name.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "market": {"type": "string", "default": "ALL"},
                            "limit": {"type": "integer", "default": 10},
                        },
                        "required": ["query"],
                    },
                },
            ),
            "get_korean_stock_profile": (
                self.service.get_profile,
                {
                    "description": "Get FinanceDataReader-backed profile metadata for a Korean stock.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"symbol_or_name": {"type": "string"}},
                        "required": ["symbol_or_name"],
                    },
                },
            ),
            "get_korean_stock_daily_history": (
                self.service.get_daily_history,
                {
                    "description": "Get daily OHLCV history for a Korean stock.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol_or_name": {"type": "string"},
                            "start_date": {"type": "string"},
                            "end_date": {"type": "string"},
                            "limit_days": {"type": "integer"},
                        },
                        "required": ["symbol_or_name"],
                    },
                },
            ),
            "get_korean_stock_intraday_10m": (
                self.service.get_intraday_10m,
                {
                    "description": "Get unofficial Naver-backed 10-minute OHLCV candles for a Korean stock.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol_or_name": {"type": "string"},
                            "start_datetime": {"type": "string"},
                            "end_datetime": {"type": "string"},
                            "lookback_days": {"type": "integer"},
                            "strict_freshness": {"type": "boolean", "default": False},
                        },
                        "required": ["symbol_or_name"],
                    },
                },
            ),
            "get_korean_stock_indicators": (
                self.service.get_indicators,
                {
                    "description": "Compute local indicators on daily or 10-minute Korean stock data.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol_or_name": {"type": "string"},
                            "timeframe": {"type": "string", "default": "1d"},
                            "lookback_days": {"type": "integer"},
                            "indicators": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["symbol_or_name"],
                    },
                },
            ),
        }

    def list_tools(self) -> list[dict]:
        payload = []
        for name, (_, meta) in self._tools.items():
            payload.append({"name": name, **meta})
        return payload

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        if name not in self._tools:
            raise KoreanStockMcpError("METHOD_NOT_FOUND", f"Unknown tool '{name}'.")
        callback, _ = self._tools[name]
        return callback(**(arguments or {}))
