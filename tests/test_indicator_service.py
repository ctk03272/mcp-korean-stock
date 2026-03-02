from korean_stock_mcp.services import IndicatorService


def test_indicator_service_returns_expected_keys() -> None:
    service = IndicatorService()
    closes = [float(100 + idx) for idx in range(40)]

    series = service.compute(closes, ["sma_20", "ema_20", "rsi_14", "macd"])

    assert len(series) == 40
    assert series[-1]["sma_20"] is not None
    assert series[-1]["ema_20"] is not None
    assert series[-1]["rsi_14"] is not None
    assert "macd" in series[-1]
    assert "macd_signal" in series[-1]
    assert "macd_hist" in series[-1]
