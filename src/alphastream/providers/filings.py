from __future__ import annotations

from dataclasses import dataclass

import requests

from alphastream.types import FilingPosition


class FilingProviderError(RuntimeError):
    """Raised when filing data cannot be fetched or normalized."""


@dataclass
class FMPFilingProvider:
    api_key: str
    base_url: str = "https://financialmodelingprep.com/stable"
    session: requests.Session | None = None
    timeout_seconds: int = 20

    def __post_init__(self) -> None:
        self.session = self.session or requests.Session()

    def fetch_positions(self, since: str | None, investor_ids: list[str]) -> list[FilingPosition]:
        filings = self._get_json("/institutional-ownership/latest", params={"apikey": self.api_key, "page": 0})
        positions: list[FilingPosition] = []
        for record in filings:
            investor_id = str(record.get("cik") or "")
            if investor_id not in investor_ids:
                continue
            date = str(record.get("date") or "")
            if not date or len(date.split("-")) < 2:
                continue
            year, month = int(date.split("-")[0]), int(date.split("-")[1])
            quarter = ((month - 1) // 3) + 1
            extract = self._get_json(
                "/institutional-ownership/extract",
                params={
                    "apikey": self.api_key,
                    "cik": investor_id,
                    "year": year,
                    "quarter": quarter,
                },
            )
            for item in extract:
                ticker = str(item.get("symbol") or "").strip().upper()
                if not ticker:
                    continue
                previous_shares = float(item.get("previousSharesNumber") or 0.0)
                shares = float(item.get("sharesNumber") or 0.0)
                change_pct = ((shares - previous_shares) / previous_shares * 100.0) if previous_shares > 0 else 100.0
                positions.append(
                    FilingPosition(
                        ticker=ticker,
                        company_name=str(item.get("securityName") or item.get("issuerName") or ticker),
                        investor_id=investor_id,
                        investor_name=str(record.get("investorName") or record.get("holder") or investor_id),
                        is_new_position=previous_shares == 0,
                        stake_increase_pct=round(change_pct, 2),
                        reported_value=float(item.get("value") or 0.0),
                        sector=str(item.get("sector") or "Unknown"),
                    )
                )
        return positions

    def _get_json(self, path: str, params: dict[str, object]) -> list[dict[str, object]]:
        assert self.session is not None
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, list):
            raise FilingProviderError(f"Unexpected filing payload for {path}")
        return payload
