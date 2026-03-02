from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass(slots=True)
class StockIdentifier:
    symbol: str
    name_ko: str
    market: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class StockSearchResult:
    identifier: StockIdentifier
    sector: str | None = None
    listing_date: date | None = None
    industry: str | None = None
    exchange: str | None = None
    match_type: str = "name_partial"

    def to_dict(self) -> dict:
        payload = asdict(self)
        if self.listing_date:
            payload["listing_date"] = self.listing_date.isoformat()
        return payload


@dataclass(slots=True)
class OHLCVBar1d:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["date"] = self.date.isoformat()
        return payload


@dataclass(slots=True)
class OHLCVBar10m:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        return payload


@dataclass(slots=True)
class FreshnessInfo:
    source: str
    as_of: datetime
    is_delayed: bool
    delay_note: str | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["as_of"] = self.as_of.isoformat()
        return payload
