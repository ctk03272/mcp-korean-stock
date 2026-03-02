from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from korean_stock_mcp.models import FreshnessInfo, OHLCVBar10m, OHLCVBar1d
from korean_stock_mcp.services import IndicatorService, MarketDataService


class StubListingProvider:
    def search(self, query: str, market: str = "ALL", limit: int = 10) -> list:
        return [
            _search_result("252670", "KODEX 200선물인버스2X"),
            _search_result("005930", "삼성전자"),
        ][:limit]

    def get_profile(self, symbol: str) -> dict:
        return {
            "symbol": symbol,
            "name_ko": "삼성전자" if symbol == "005930" else "KODEX 200선물인버스2X",
            "market": "KOSPI",
            "sector": "전자",
            "industry": "반도체",
            "exchange": "KRX",
            "listing_date": date(1975, 6, 11),
        }


class StubDailyProvider:
    def get_daily_bars(self, symbol: str, start_date=None, end_date=None) -> list[OHLCVBar1d]:
        return [
            OHLCVBar1d(date=date(2026, 2, 27), open=100, high=110, low=90, close=105, volume=1000),
            OHLCVBar1d(date=date(2026, 2, 28), open=106, high=112, low=101, close=110, volume=1100),
        ]


class StubIntradayProvider:
    base_url = "https://api.stock.naver.com/chart/domestic/item/{symbol}/minute10"

    def get_10m_bars(self, symbol: str, start_datetime: datetime, end_datetime: datetime):
        tz = ZoneInfo("Asia/Seoul")
        bars = [
            OHLCVBar10m(
                timestamp=datetime(2026, 3, 2, 14, 0, tzinfo=tz),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=5000.0,
            ),
            OHLCVBar10m(
                timestamp=datetime(2026, 3, 2, 14, 10, tzinfo=tz),
                open=100.5,
                high=102.0,
                low=100.0,
                close=101.5,
                volume=5500.0,
            ),
        ]
        freshness = FreshnessInfo(
            source="naver-minute10",
            as_of=bars[-1].timestamp,
            is_delayed=False,
            delay_note="Naver intraday data is unofficial and may be delayed.",
        )
        return bars, freshness


def _search_result(symbol: str, name_ko: str):
    from korean_stock_mcp.models import StockIdentifier, StockSearchResult

    return StockSearchResult(
        identifier=StockIdentifier(symbol=symbol, name_ko=name_ko, market="KOSPI"),
        sector="전자",
        industry="반도체",
        exchange="KRX",
        match_type="symbol_exact" if symbol == "005930" else "name_partial",
    )


def build_service() -> MarketDataService:
    return MarketDataService(
        listing_provider=StubListingProvider(),
        daily_provider=StubDailyProvider(),
        intraday_provider=StubIntradayProvider(),
        indicator_service=IndicatorService(),
    )


def test_get_profile_returns_fdr_backed_fields() -> None:
    profile = build_service().get_profile("005930")

    assert profile["symbol"] == "005930"
    assert profile["source"] == "FinanceDataReader"


def test_get_daily_history_returns_bars() -> None:
    history = build_service().get_daily_history("005930", limit_days=1)

    assert len(history["bars"]) == 1
    assert history["bars"][0]["close"] == 110


def test_get_intraday_10m_returns_canonical_payload() -> None:
    payload = build_service().get_intraday_10m("005930", lookback_days=1)

    assert payload["interval"] == "10m"
    assert len(payload["bars"]) == 2
    assert payload["source"] == "naver-minute10"


def test_get_indicators_uses_requested_timeframe() -> None:
    payload = build_service().get_indicators("005930", timeframe="10m")

    assert payload["timeframe"] == "10m"
    assert len(payload["series"]) == 2
