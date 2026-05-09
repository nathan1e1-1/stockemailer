from __future__ import annotations

from typing import Protocol

from alphastream.types import FilingPosition, Headline, MarketSnapshot


class FilingProvider(Protocol):
    def fetch_positions(self, since: str | None, investor_ids: list[str]) -> list[FilingPosition]:
        ...


class NewsProvider(Protocol):
    def fetch_headlines(self, ticker: str, lookback_hours: int = 48) -> list[Headline]:
        ...


class MarketDataProvider(Protocol):
    def fetch_snapshot(self, ticker: str) -> MarketSnapshot:
        ...
