from __future__ import annotations

from datetime import date, datetime

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.models import OHLCVBar1d, StockIdentifier, StockSearchResult


class FdrListingProvider:
    def __init__(self) -> None:
        self._listing_cache: list[dict] | None = None

    def _load_listing(self) -> list[dict]:
        if self._listing_cache is not None:
            return self._listing_cache
        try:
            import FinanceDataReader as fdr
        except ImportError as exc:
            raise KoreanStockMcpError("UPSTREAM_UNAVAILABLE", "FinanceDataReader is not installed.") from exc

        records: list[dict] = []
        for market in ("KOSPI", "KOSDAQ"):
            frame = fdr.StockListing(market)
            for row in frame.to_dict(orient="records"):
                symbol = str(row.get("Code", "")).zfill(6)
                if not symbol:
                    continue
                records.append(
                    {
                        "symbol": symbol,
                        "name_ko": row.get("Name", ""),
                        "market": row.get("Market", market),
                        "sector": row.get("Sector"),
                        "industry": row.get("Industry"),
                        "exchange": row.get("Exchange"),
                        "listing_date": self._parse_date(row.get("ListingDate")),
                    }
                )
        self._listing_cache = records
        return records

    @staticmethod
    def _parse_date(value: object) -> date | None:
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        text = str(value)
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _normalize_query(query: str) -> str:
        return "".join(query.lower().split())

    def search(self, query: str, market: str = "ALL", limit: int = 10) -> list[StockSearchResult]:
        normalized = self._normalize_query(query)
        candidates: list[StockSearchResult] = []
        for row in self._load_listing():
            if market != "ALL" and row["market"] != market:
                continue
            symbol = row["symbol"]
            name = row["name_ko"]
            normalized_name = self._normalize_query(name)
            match_type = None
            if query.isdigit() and len(query) <= 6 and symbol == query.zfill(6):
                match_type = "symbol_exact"
            elif normalized_name == normalized:
                match_type = "name_exact"
            elif normalized in normalized_name:
                match_type = "name_partial"
            if match_type is None:
                continue
            candidates.append(
                StockSearchResult(
                    identifier=StockIdentifier(symbol=symbol, name_ko=name, market=row["market"]),
                    sector=row["sector"],
                    listing_date=row["listing_date"],
                    industry=row["industry"],
                    exchange=row["exchange"],
                    match_type=match_type,
                )
            )
        sort_order = {"symbol_exact": 0, "name_exact": 1, "name_partial": 2}
        candidates.sort(key=lambda item: (sort_order[item.match_type], item.identifier.symbol))
        return candidates[:limit]

    def get_profile(self, symbol: str) -> dict:
        for row in self._load_listing():
            if row["symbol"] == symbol:
                return row
        raise KoreanStockMcpError("SYMBOL_NOT_FOUND", f"Symbol '{symbol}' was not found.")


class FdrDailyMarketDataProvider:
    def get_daily_bars(
        self,
        symbol: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[OHLCVBar1d]:
        try:
            import FinanceDataReader as fdr
        except ImportError as exc:
            raise KoreanStockMcpError("UPSTREAM_UNAVAILABLE", "FinanceDataReader is not installed.") from exc

        frame = fdr.DataReader(symbol, start_date, end_date)
        if frame.empty:
            return []

        bars: list[OHLCVBar1d] = []
        for index, row in frame.sort_index().iterrows():
            bars.append(
                OHLCVBar1d(
                    date=index.date(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0.0)),
                )
            )
        return bars
