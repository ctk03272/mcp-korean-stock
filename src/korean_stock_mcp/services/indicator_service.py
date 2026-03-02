from __future__ import annotations

from collections.abc import Sequence


class IndicatorService:
    def compute(self, closes: Sequence[float], indicators: list[str]) -> list[dict]:
        rows = [{"close": close} for close in closes]
        if "sma_20" in indicators:
            self._attach_sma(rows, window=20, key="sma_20")
        if "ema_20" in indicators:
            self._attach_ema(rows, window=20, key="ema_20")
        if "rsi_14" in indicators:
            self._attach_rsi(rows, window=14, key="rsi_14")
        if "macd" in indicators:
            self._attach_macd(rows)
        return rows

    def _attach_sma(self, rows: list[dict], window: int, key: str) -> None:
        for index in range(len(rows)):
            if index + 1 < window:
                rows[index][key] = None
                continue
            values = [row["close"] for row in rows[index - window + 1:index + 1]]
            rows[index][key] = sum(values) / window

    def _attach_ema(self, rows: list[dict], window: int, key: str) -> None:
        multiplier = 2 / (window + 1)
        ema = None
        for index, row in enumerate(rows):
            close = row["close"]
            if ema is None:
                ema = close
            else:
                ema = (close - ema) * multiplier + ema
            row[key] = ema if index + 1 >= window else None

    def _attach_rsi(self, rows: list[dict], window: int, key: str) -> None:
        gains: list[float] = []
        losses: list[float] = []
        rows[0][key] = None
        for index in range(1, len(rows)):
            delta = rows[index]["close"] - rows[index - 1]["close"]
            gains.append(max(delta, 0.0))
            losses.append(abs(min(delta, 0.0)))
            if index < window:
                rows[index][key] = None
                continue
            avg_gain = sum(gains[-window:]) / window
            avg_loss = sum(losses[-window:]) / window
            if avg_loss == 0:
                rows[index][key] = 100.0
                continue
            rs = avg_gain / avg_loss
            rows[index][key] = 100 - (100 / (1 + rs))

    def _attach_macd(self, rows: list[dict]) -> None:
        ema12 = self._ema_series([row["close"] for row in rows], 12)
        ema26 = self._ema_series([row["close"] for row in rows], 26)
        macd_values: list[float | None] = []
        for index, row in enumerate(rows):
            if ema12[index] is None or ema26[index] is None:
                row["macd"] = None
                row["macd_signal"] = None
                row["macd_hist"] = None
                macd_values.append(None)
                continue
            macd = float(ema12[index] - ema26[index])
            macd_values.append(macd)
            row["macd"] = macd
        signal_values = self._ema_series([value if value is not None else 0.0 for value in macd_values], 9)
        for index, row in enumerate(rows):
            if row["macd"] is None or signal_values[index] is None:
                row["macd_signal"] = None
                row["macd_hist"] = None
                continue
            row["macd_signal"] = signal_values[index]
            row["macd_hist"] = row["macd"] - row["macd_signal"]

    def _ema_series(self, values: list[float], window: int) -> list[float | None]:
        multiplier = 2 / (window + 1)
        ema: float | None = None
        result: list[float | None] = []
        for index, value in enumerate(values):
            if ema is None:
                ema = value
            else:
                ema = (value - ema) * multiplier + ema
            result.append(ema if index + 1 >= window else None)
        return result
