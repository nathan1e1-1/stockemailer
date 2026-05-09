from alphastream.scoring import ScoringEngine
from alphastream.types import CandidateSignal, FilingPosition, Headline, MarketSnapshot


def build_candidate(
    *,
    is_new_position: bool = True,
    stake_increase_pct: float = 12.0,
    sector: str = "Technology",
    news_title: str = "Company signs AI infrastructure contract and beats earnings",
    price: float = 210.0,
    moving_average_200: float = 190.0,
    rsi_14: float = 55.0,
    market_cap: float = 800_000_000.0,
) -> CandidateSignal:
    return CandidateSignal(
        filing=FilingPosition(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            investor_id="berkshire-hathaway",
            investor_name="Berkshire Hathaway",
            is_new_position=is_new_position,
            stake_increase_pct=stake_increase_pct,
            reported_value=1_000_000.0,
            sector=sector,
        ),
        headlines=[Headline(title=news_title, summary="summary", published_at="2026-05-08T10:00:00Z")],
        market=MarketSnapshot(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            market_cap=market_cap,
            sector=sector,
            current_price=price,
            moving_average_200=moving_average_200,
            rsi_14=rsi_14,
        ),
        strategy_label="AI Tech",
    )


def test_score_favors_new_position_positive_sentiment_and_bullish_trend() -> None:
    engine = ScoringEngine(
        weights={"institutional": 0.4, "sentiment": 0.3, "technical": 0.3},
        overbought_rsi=70.0,
        strong_signal_threshold=80,
    )

    result = engine.score(build_candidate())

    assert result.total_score == 100
    assert result.signal_label == "Strong Signal"
    assert result.institutional_score == 100
    assert result.sentiment_score == 100
    assert result.technical_score == 100


def test_score_penalizes_overbought_and_negative_sentiment() -> None:
    engine = ScoringEngine(
        weights={"institutional": 0.4, "sentiment": 0.3, "technical": 0.3},
        overbought_rsi=70.0,
        strong_signal_threshold=80,
    )

    result = engine.score(
        build_candidate(
            is_new_position=False,
            stake_increase_pct=5.0,
            news_title="Company faces lawsuit and analyst downgrade",
            price=180.0,
            moving_average_200=200.0,
            rsi_14=78.0,
        )
    )

    assert result.total_score == 0
    assert result.signal_label == "Watch"
    assert result.institutional_score == 0
    assert result.sentiment_score == 0
    assert result.technical_score == 0
