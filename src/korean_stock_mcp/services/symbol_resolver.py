from __future__ import annotations

from korean_stock_mcp.cache import TTLCache
from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.models import StockSearchResult
from korean_stock_mcp.providers import FdrListingProvider


class SymbolResolver:
    def __init__(self, listing_provider: FdrListingProvider, ttl_seconds: int = 600) -> None:
        self.listing_provider = listing_provider
        self.cache = TTLCache(maxsize=512, ttl=ttl_seconds)

    def search(self, query: str, market: str = "ALL", limit: int = 10) -> list[StockSearchResult]:
        cache_key = (query, market, limit)
        if cache_key not in self.cache:
            self.cache[cache_key] = self.listing_provider.search(query=query, market=market, limit=limit)
        return self.cache[cache_key]

    def resolve(self, symbol_or_name: str) -> StockSearchResult:
        if symbol_or_name.isdigit():
            normalized = symbol_or_name.zfill(6)
        else:
            normalized = symbol_or_name

        results = self.search(normalized, limit=10)
        if not results:
            raise KoreanStockMcpError("SYMBOL_NOT_FOUND", f"No Korean stock matched '{symbol_or_name}'.")

        exact = [
            result for result in results
            if result.identifier.symbol == normalized or result.identifier.name_ko == symbol_or_name
        ]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise KoreanStockMcpError(
                "SYMBOL_AMBIGUOUS",
                f"Multiple stocks matched '{symbol_or_name}'.",
                {"candidates": [result.to_dict() for result in exact]},
            )
        if len(results) > 1 and results[0].match_type == "name_partial":
            raise KoreanStockMcpError(
                "SYMBOL_AMBIGUOUS",
                f"Multiple stocks matched '{symbol_or_name}'.",
                {"candidates": [result.to_dict() for result in results]},
            )
        return results[0]
