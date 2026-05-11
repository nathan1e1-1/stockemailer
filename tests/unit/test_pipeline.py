from datetime import date

from alphastream.pipeline import classify_strategy, filter_candidates, partition_ranked_picks
from alphastream.types import CandidateSignal, FilingPosition, Headline, MarketSnapshot, RankedPick, ScoreBreakdown


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


def test_partition_ranked_picks_creates_top_picks_and_watchlist_to_target_size() -> None:
    ranked = [
        RankedPick(
            ticker="AAA",
            company_name="AAA Inc.",
            investor_name="Fund A",
            strategy_label="AI Tech",
            whale_note="New position opened",
            sentiment_note="Positive",
            trend_note="Bullish",
            market_cap=1_000_000_000.0,
            current_price=100.0,
            moving_average_200=90.0,
            rsi_14=55.0,
            section="unassigned",
            score=ScoreBreakdown(total_score=100, signal_label="Strong Signal", institutional_score=100, sentiment_score=100, technical_score=100),
        ),
        RankedPick(
            ticker="BBB",
            company_name="BBB Inc.",
            investor_name="Fund B",
            strategy_label="Energy Play",
            whale_note="Position increased by 15.0%",
            sentiment_note="Positive",
            trend_note="Bullish",
            market_cap=900_000_000.0,
            current_price=90.0,
            moving_average_200=85.0,
            rsi_14=58.0,
            section="unassigned",
            score=ScoreBreakdown(total_score=85, signal_label="Strong Signal", institutional_score=100, sentiment_score=50, technical_score=100),
        ),
        RankedPick(
            ticker="CCC",
            company_name="CCC Inc.",
            investor_name="Fund C",
            strategy_label="Value Rotation",
            whale_note="Position increased by 5.0%",
            sentiment_note="Neutral",
            trend_note="Mixed",
            market_cap=850_000_000.0,
            current_price=75.0,
            moving_average_200=76.0,
            rsi_14=61.0,
            section="unassigned",
            score=ScoreBreakdown(total_score=65, signal_label="Watch", institutional_score=0, sentiment_score=100, technical_score=100),
        ),
        RankedPick(
            ticker="DDD",
            company_name="DDD Inc.",
            investor_name="Fund D",
            strategy_label="AI Tech",
            whale_note="Position increased by 4.0%",
            sentiment_note="Neutral",
            trend_note="Mixed",
            market_cap=820_000_000.0,
            current_price=60.0,
            moving_average_200=61.0,
            rsi_14=63.0,
            section="unassigned",
            score=ScoreBreakdown(total_score=50, signal_label="Watch", institutional_score=0, sentiment_score=50, technical_score=100),
        ),
    ]

    selected = partition_ranked_picks(
        ranked,
        top_pick_min_score=80,
        watchlist_min_score=50,
        max_top_picks=2,
        target_total_picks=4,
    )

    assert [(pick.ticker, pick.section) for pick in selected] == [
        ("AAA", "top_pick"),
        ("BBB", "top_pick"),
        ("CCC", "watchlist"),
        ("DDD", "watchlist"),
    ]
