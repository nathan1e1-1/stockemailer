from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from alphastream.types import Headline


@dataclass
class FinnhubNewsProvider:
    api_key: str
    base_url: str = "https://finnhub.io/api/v1"
    session: requests.Session | None = None
    timeout_seconds: int = 20

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()

    def fetch_headlines(self, ticker: str, lookback_hours: int = 48) -> list[Headline]:
        assert self.session is not None
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=lookback_hours)
        response = self.session.get(
            f"{self.base_url}/company-news",
            params={
                "token": self.api_key,
                "symbol": ticker,
                "from": start_time.date().isoformat(),
                "to": end_time.date().isoformat(),
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [
            Headline(
                title=str(item.get("headline") or ""),
                summary=str(item.get("summary") or ""),
                published_at=datetime.fromtimestamp(int(item.get("datetime") or 0), tz=timezone.utc).isoformat(),
            )
            for item in payload
            if item.get("headline")
        ]
