from datetime import date

from alphastream.pipeline import classify_strategy, filter_candidates
from alphastream.types import CandidateSignal, FilingPosition, Headline, MarketSnapshot


def build_candidate(ticker: str, sector: str, market_cap: float, strategy_label: str) -> CandidateSignal:
    return CandidateSignal(
        filing=FilingPosition(
            ticker=ticker,
            company_name=f"{ticker} Inc.",
            investor_id="fund",
            investor_name="Fund",
            is_new_position=True,
            stake_increase_pct=15.0,
            reported_value=5_000_000.0,
            sector=sector,
        ),
        headlines=[Headline(title=f"{ticker} expands infrastructure", summary="summary", published_at="2026-05-08T10:00:00Z")],
        market=MarketSnapshot(
            ticker=ticker,
            company_name=f"{ticker} Inc.",
            market_cap=market_cap,
            sector=sector,
            current_price=100.0,
            moving_average_200=90.0,
            rsi_14=50.0,
        ),
        strategy_label=strategy_label,
    )


def test_classify_strategy_uses_sector_and_keyword_matching() -> None:
    sector_map = {
        "ai_tech": {"label": "AI Tech", "sectors": ["Technology"], "keywords": ["ai", "cloud"]},
        "energy_play": {"label": "Energy Play", "sectors": ["Utilities"], "keywords": ["grid"]},
    }

    strategy = classify_strategy("Technology", "AI cloud platform expands", sector_map)

    assert strategy == "AI Tech"


def test_filter_candidates_applies_market_cap_and_recent_send_dedupe() -> None:
    candidates = [
        build_candidate("KEEP", "Technology", 900_000_000.0, "AI Tech"),
        build_candidate("SMALL", "Technology", 400_000_000.0, "AI Tech"),
        build_candidate("OLD", "Utilities", 900_000_000.0, "Energy Play"),
    ]

    filtered = filter_candidates(
        candidates,
        market_cap_min=500_000_000.0,
        recently_sent={"OLD": date(2026, 4, 20)},
        today=date(2026, 5, 8),
        dedupe_days=30,
    )

    assert [candidate.filing.ticker for candidate in filtered] == ["KEEP"]
