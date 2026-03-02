from __future__ import annotations

import os

from korean_stock_mcp.providers import FdrDailyMarketDataProvider, FdrListingProvider, NaverIntraday10mProvider
from korean_stock_mcp.services import IndicatorService, MarketDataService
from korean_stock_mcp.tools import ToolRegistry
from korean_stock_mcp.transports import run_http_server, run_stdio_server


def build_registry() -> ToolRegistry:
    service = MarketDataService(
        listing_provider=FdrListingProvider(),
        daily_provider=FdrDailyMarketDataProvider(),
        intraday_provider=NaverIntraday10mProvider(timezone_name=os.getenv("MARKET_TZ", "Asia/Seoul")),
        indicator_service=IndicatorService(),
        timezone_name=os.getenv("MARKET_TZ", "Asia/Seoul"),
    )
    return ToolRegistry(service)


def main() -> None:
    registry = build_registry()
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport == "http":
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_PORT", "8000"))
        run_http_server(registry, host=host, port=port)
        return
    run_stdio_server(registry)


if __name__ == "__main__":
    main()
