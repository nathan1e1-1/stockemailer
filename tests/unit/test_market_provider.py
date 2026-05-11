from __future__ import annotations

import warnings

import alphastream.providers.market as market_module
from alphastream.providers.market import YFinanceMarketDataProvider


class FakeCloseSeries:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class FakeHistory:
    def __init__(self, closes: list[float]) -> None:
        self._closes = closes

    def __getitem__(self, key: str) -> FakeCloseSeries:
        assert key == "Close"
        return FakeCloseSeries(self._closes)


class FakeTicker:
    @property
    def info(self) -> dict[str, object]:
        warnings.warn(
            "Timestamp.utcnow is deprecated and will be removed in a future version. Use Timestamp.now('UTC') instead.",
            FutureWarning,
            stacklevel=1,
        )
        return {"longName": "NVIDIA Corporation", "marketCap": 1000000000.0, "sector": "Technology"}

    def history(self, period: str, auto_adjust: bool = False) -> FakeHistory:
        warnings.warn(
            "Timestamp.utcnow is deprecated and will be removed in a future version. Use Timestamp.now('UTC') instead.",
            FutureWarning,
            stacklevel=1,
        )
        return FakeHistory([100.0 + index for index in range(30)])


def test_market_provider_suppresses_known_yfinance_timestamp_warning(monkeypatch) -> None:
    monkeypatch.setattr(market_module.yf, "Ticker", lambda ticker: FakeTicker())
    provider = YFinanceMarketDataProvider()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        snapshot = provider.fetch_snapshot("NVDA")

    assert snapshot.ticker == "NVDA"
    assert caught == []
