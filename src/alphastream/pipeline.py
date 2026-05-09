from __future__ import annotations

from datetime import date

from alphastream.types import CandidateSignal


def classify_strategy(sector: str, text: str, sector_map: dict[str, dict[str, object]]) -> str | None:
    lowered_sector = sector.lower()
    lowered_text = text.lower()
    for definition in sector_map.values():
        sectors = [item.lower() for item in definition.get("sectors", [])]
        keywords = [item.lower() for item in definition.get("keywords", [])]
        if lowered_sector in sectors or any(keyword in lowered_text for keyword in keywords):
            return str(definition["label"])
    return None


def filter_candidates(
    candidates: list[CandidateSignal],
    *,
    market_cap_min: float,
    recently_sent: dict[str, date],
    today: date,
    dedupe_days: int,
) -> list[CandidateSignal]:
    filtered: list[CandidateSignal] = []
    for candidate in candidates:
        ticker = candidate.filing.ticker.upper()
        last_sent = recently_sent.get(ticker)
        within_window = last_sent is not None and (today - last_sent).days < dedupe_days
        if candidate.market.market_cap < market_cap_min or within_window:
            continue
        filtered.append(candidate)
    return filtered
