from __future__ import annotations

from dataclasses import replace
from datetime import date

from alphastream.types import CandidateSignal, RankedPick


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


def partition_ranked_picks(
    ranked_picks: list[RankedPick],
    *,
    top_pick_min_score: int,
    watchlist_min_score: int,
    max_top_picks: int,
    target_total_picks: int,
) -> list[RankedPick]:
    top_picks = [
        replace(pick, section="top_pick")
        for pick in ranked_picks
        if pick.score.total_score >= top_pick_min_score
    ][:max_top_picks]
    selected_tickers = {pick.ticker for pick in top_picks}
    remaining_slots = max(target_total_picks - len(top_picks), 0)
    watchlist = [
        replace(pick, section="watchlist")
        for pick in ranked_picks
        if pick.ticker not in selected_tickers and pick.score.total_score >= watchlist_min_score
    ][:remaining_slots]
    return top_picks + watchlist
