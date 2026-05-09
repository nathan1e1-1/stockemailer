from __future__ import annotations

from dataclasses import dataclass

import yfinance as yf

from alphastream.types import MarketSnapshot


def _compute_rsi(prices: list[float], window: int = 14) -> float:
    if len(prices) <= window:
        return 50.0
    gains = []
    losses = []
    for current, previous in zip(prices[1:], prices[:-1]):
        delta = current - previous
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    average_gain = sum(gains[-window:]) / window
    average_loss = sum(losses[-window:]) / window
    if average_loss == 0:
        return 100.0 if average_gain > 0 else 50.0
    relative_strength = average_gain / average_loss
    return round(100 - (100 / (1 + relative_strength)), 2)


@dataclass
class YFinanceMarketDataProvider:
    history_period: str = "1y"

    def fetch_snapshot(self, ticker: str) -> MarketSnapshot:
        stock = yf.Ticker(ticker)
        info = stock.info
        history = stock.history(period=self.history_period, auto_adjust=False)
        closes = [float(value) for value in history["Close"].tolist() if value == value]
        if not closes:
            raise RuntimeError(f"No market history available for {ticker}")
        moving_average_200 = round(sum(closes[-200:]) / min(len(closes), 200), 2)
        return MarketSnapshot(
            ticker=ticker,
            company_name=str(info.get("longName") or ticker),
            market_cap=float(info.get("marketCap") or 0.0),
            sector=str(info.get("sector") or "Unknown"),
            current_price=round(closes[-1], 2),
            moving_average_200=moving_average_200,
            rsi_14=_compute_rsi(closes, window=14),
        )
