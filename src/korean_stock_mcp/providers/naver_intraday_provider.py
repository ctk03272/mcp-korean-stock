from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.models import FreshnessInfo, OHLCVBar10m


class NaverIntraday10mProvider:
    base_url = "https://api.stock.naver.com/chart/domestic/item/{symbol}/minute10"

    def __init__(self, timezone_name: str = "Asia/Seoul") -> None:
        self.timezone = ZoneInfo(timezone_name)

    def get_10m_bars(self, symbol: str, start_datetime: datetime, end_datetime: datetime) -> tuple[list[OHLCVBar10m], FreshnessInfo]:
        try:
            import httpx
        except ImportError as exc:
            raise KoreanStockMcpError("UPSTREAM_UNAVAILABLE", "httpx is not installed.") from exc

        params = {
            "startDateTime": start_datetime.strftime("%Y%m%d%H%M"),
            "endDateTime": end_datetime.strftime("%Y%m%d%H%M"),
        }
        url = self.base_url.format(symbol=symbol)

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise KoreanStockMcpError("UPSTREAM_UNAVAILABLE", "Failed to fetch Naver intraday data.") from exc

        bars = self._parse_payload(payload)
        if not bars:
            raise KoreanStockMcpError("UPSTREAM_UNAVAILABLE", "No Naver intraday data was returned.")

        latest = bars[-1].timestamp
        now = datetime.now(self.timezone)
        freshness = FreshnessInfo(
            source="naver-minute10",
            as_of=latest,
            is_delayed=(now - latest) > timedelta(minutes=20),
            delay_note="Naver intraday data is unofficial and may be delayed.",
        )
        return bars, freshness

    def _parse_payload(self, payload: object) -> list[OHLCVBar10m]:
        if not isinstance(payload, dict):
            raise KoreanStockMcpError("UPSTREAM_SCHEMA_CHANGED", "Unexpected Naver payload root.")
        items = payload.get("items") or payload.get("chartData") or payload.get("datas")
        if not isinstance(items, list):
            raise KoreanStockMcpError("UPSTREAM_SCHEMA_CHANGED", "Unexpected Naver intraday items shape.")

        bars: list[OHLCVBar10m] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            timestamp = item.get("localTradedAt") or item.get("time") or item.get("dt")
            open_price = item.get("openPrice") or item.get("open")
            high_price = item.get("highPrice") or item.get("high")
            low_price = item.get("lowPrice") or item.get("low")
            close_price = item.get("closePrice") or item.get("close")
            volume = item.get("accumulatedTradingVolume") or item.get("volume") or 0
            if None in (timestamp, open_price, high_price, low_price, close_price):
                continue
            bars.append(
                OHLCVBar10m(
                    timestamp=self._parse_timestamp(str(timestamp)),
                    open=float(open_price),
                    high=float(high_price),
                    low=float(low_price),
                    close=float(close_price),
                    volume=float(volume),
                )
            )

        bars.sort(key=lambda bar: bar.timestamp)
        return bars

    def _parse_timestamp(self, value: str) -> datetime:
        formats = ("%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M", "%Y-%m-%dT%H:%M:%S")
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=self.timezone)
            except ValueError:
                continue
        raise KoreanStockMcpError("UPSTREAM_SCHEMA_CHANGED", f"Unexpected intraday timestamp format: {value}")
