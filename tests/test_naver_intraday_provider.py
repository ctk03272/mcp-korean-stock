from datetime import datetime

import pytest

from korean_stock_mcp.errors import KoreanStockMcpError
from korean_stock_mcp.providers import NaverIntraday10mProvider


def test_parse_payload_supports_known_shape() -> None:
    provider = NaverIntraday10mProvider()
    payload = {
        "items": [
            {
                "localTradedAt": "2026-03-02 14:10:00",
                "openPrice": 100,
                "highPrice": 110,
                "lowPrice": 99,
                "closePrice": 105,
                "accumulatedTradingVolume": 1234,
            }
        ]
    }

    bars = provider._parse_payload(payload)

    assert len(bars) == 1
    assert bars[0].timestamp == datetime(2026, 3, 2, 14, 10, tzinfo=provider.timezone)


def test_parse_payload_rejects_unknown_shape() -> None:
    provider = NaverIntraday10mProvider()

    with pytest.raises(KoreanStockMcpError) as exc:
        provider._parse_payload({"unexpected": []})

    assert exc.value.code == "UPSTREAM_SCHEMA_CHANGED"
