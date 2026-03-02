from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from korean_stock_mcp.cache import TTLCache
from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.providers import FdrDailyMarketDataProvider, FdrListingProvider, NaverIntraday10mProvider
from korean_stock_mcp.services.indicator_service import IndicatorService
from korean_stock_mcp.services.symbol_resolver import SymbolResolver


class MarketDataService:
    def __init__(
        self,
        listing_provider: FdrListingProvider,
        daily_provider: FdrDailyMarketDataProvider,
        intraday_provider: NaverIntraday10mProvider,
        indicator_service: IndicatorService,
        timezone_name: str = "Asia/Seoul",
    ) -> None:
        self.resolver = SymbolResolver(listing_provider)
        self.listing_provider = listing_provider
        self.daily_provider = daily_provider
        self.intraday_provider = intraday_provider
        self.indicator_service = indicator_service
        self.timezone = ZoneInfo(timezone_name)
        self.daily_cache = TTLCache(maxsize=256, ttl=900)
        self.intraday_cache = TTLCache(maxsize=256, ttl=60)
        self.profile_cache = TTLCache(maxsize=256, ttl=600)

    def search_stocks(self, query: str, market: str = "ALL", limit: int = 10) -> dict:
        results = self.resolver.search(query, market=market, limit=limit)
        return {"results": [item.to_dict() for item in results], "source": "FinanceDataReader"}

    def get_profile(self, symbol_or_name: str) -> dict:
        resolved = self.resolver.resolve(symbol_or_name)
        symbol = resolved.identifier.symbol
        if symbol not in self.profile_cache:
            profile = self.listing_provider.get_profile(symbol)
            self.profile_cache[symbol] = {
                "symbol": profile["symbol"],
                "name_ko": profile["name_ko"],
                "market": profile["market"],
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "listing_date": profile["listing_date"].isoformat() if profile.get("listing_date") else None,
                "exchange": profile.get("exchange"),
                "source": "FinanceDataReader",
            }
        return self.profile_cache[symbol]

    def get_daily_history(
        self,
        symbol_or_name: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit_days: int | None = None,
    ) -> dict:
        resolved = self.resolver.resolve(symbol_or_name)
        start = self._parse_date(start_date) if start_date else None
        end = self._parse_date(end_date) if end_date else None
        if start and end and start > end:
            raise KoreanStockMcpError("INVALID_DATE_RANGE", "start_date must be before end_date.")
        if not start and not end:
            end = date.today()
            start = end - timedelta(days=180)
        cache_key = (resolved.identifier.symbol, start, end)
        if cache_key not in self.daily_cache:
            self.daily_cache[cache_key] = self.daily_provider.get_daily_bars(resolved.identifier.symbol, start, end)
        bars = self.daily_cache[cache_key]
        if limit_days is not None:
            bars = bars[-limit_days:]
        return {
            "symbol": resolved.identifier.symbol,
            "name_ko": resolved.identifier.name_ko,
            "timezone": self.timezone.key,
            "bars": [bar.to_dict() for bar in bars],
            "source": "FinanceDataReader",
        }

    def get_intraday_10m(
        self,
        symbol_or_name: str,
        start_datetime: str | None = None,
        end_datetime: str | None = None,
        lookback_days: int | None = None,
        strict_freshness: bool = False,
    ) -> dict:
        resolved = self.resolver.resolve(symbol_or_name)
        end = self._parse_datetime(end_datetime) if end_datetime else datetime.now(self.timezone)
        if start_datetime:
            start = self._parse_datetime(start_datetime)
        else:
            start = end - timedelta(days=lookback_days or 5)
        cache_key = (resolved.identifier.symbol, start, end)
        if cache_key not in self.intraday_cache:
            self.intraday_cache[cache_key] = self.intraday_provider.get_10m_bars(resolved.identifier.symbol, start, end)
        bars, freshness = self.intraday_cache[cache_key]
        if strict_freshness:
            max_age = datetime.now(self.timezone) - timedelta(minutes=20)
            if freshness.as_of < max_age:
                raise KoreanStockMcpError("STALE_INTRADAY_DATA", "Intraday data is stale.", freshness.to_dict())
        return {
            "symbol": resolved.identifier.symbol,
            "name_ko": resolved.identifier.name_ko,
            "interval": "10m",
            "timezone": self.timezone.key,
            "bars": [bar.to_dict() for bar in bars],
            "latest_bar_timestamp": freshness.as_of.isoformat(),
            "source": freshness.source,
            "source_url_template": self.intraday_provider.base_url,
            "is_delayed": freshness.is_delayed,
            "delay_note": freshness.delay_note,
        }

    def get_indicators(
        self,
        symbol_or_name: str,
        timeframe: str = "1d",
        lookback_days: int | None = None,
        indicators: list[str] | None = None,
    ) -> dict:
        indicators = indicators or ["sma_20", "ema_20", "rsi_14", "macd"]
        resolved = self.resolver.resolve(symbol_or_name)
        if timeframe == "1d":
            history = self.get_daily_history(symbol_or_name, limit_days=lookback_days or 90)
            labels = [bar["date"] for bar in history["bars"]]
        elif timeframe == "10m":
            history = self.get_intraday_10m(symbol_or_name, lookback_days=lookback_days or 5)
            labels = [bar["timestamp"] for bar in history["bars"]]
        else:
            raise KoreanStockMcpError("INVALID_LOOKBACK", f"Unsupported timeframe '{timeframe}'.")
        closes = [bar["close"] for bar in history["bars"]]
        series = self.indicator_service.compute(closes, indicators)
        merged = []
        for label, metrics in zip(labels, series, strict=True):
            row = {"timestamp_or_date": label}
            row.update(metrics)
            merged.append(row)
        return {
            "symbol": resolved.identifier.symbol,
            "name_ko": resolved.identifier.name_ko,
            "timeframe": timeframe,
            "source_series": history["source"],
            "series": merged,
        }

    @staticmethod
    def _parse_date(value: str) -> date:
        return datetime.strptime(value, "%Y-%m-%d").date()

    def _parse_datetime(self, value: str) -> datetime:
        parsed = datetime.strptime(value, "%Y%m%d%H%M")
        return parsed.replace(tzinfo=self.timezone)
