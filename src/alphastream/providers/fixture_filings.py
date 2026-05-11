from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from alphastream.types import FilingPosition


@dataclass(frozen=True)
class LocalFixtureFilingProvider:
    fixture_path: Path

    def fetch_positions(self, since: str | None, investor_ids: list[str]) -> list[FilingPosition]:
        payload = json.loads(self.fixture_path.read_text())
        positions: list[FilingPosition] = []
        for item in payload:
            investor_id = str(item.get("investor_id") or "")
            if investor_ids and investor_id not in investor_ids:
                continue
            positions.append(
                FilingPosition(
                    ticker=str(item["ticker"]).upper(),
                    company_name=str(item["company_name"]),
                    investor_id=investor_id,
                    investor_name=str(item["investor_name"]),
                    is_new_position=bool(item["is_new_position"]),
                    stake_increase_pct=float(item["stake_increase_pct"]),
                    reported_value=float(item["reported_value"]),
                    sector=str(item["sector"]),
                )
            )
        return positions
