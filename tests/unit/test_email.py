from alphastream.email.render import render_email
from alphastream.types import EmailReport, RankedPick, ScoreBreakdown


def test_render_email_sanitizes_hostile_content() -> None:
    picks = [
        RankedPick(
            ticker="EVIL<script>",
            company_name='Bad & Co <img src=x onerror="alert(1)">',
            investor_name="Fund",
            sector="Technology",
            strategy_label="AI Tech",
            whale_note='New position <b>opened</b>',
            sentiment_note='Contract <b>won</b> & "safe"',
            trend_note="Bullish above 200-day MA",
            headline_summary='Lead headline <b>summary</b>',
            reported_value=125000000.0,
            market_cap=880000000.0,
            current_price=130.25,
            moving_average_200=120.10,
            rsi_14=55.0,
            score=ScoreBreakdown(
                total_score=88,
                signal_label="Strong Signal",
                institutional_score=100,
                sentiment_score=80,
                technical_score=80,
            ),
            section="top_pick",
        ),
        RankedPick(
            ticker="WATCH",
            company_name="Watch Co",
            investor_name="Fund",
            sector="Utilities",
            strategy_label="Energy Play",
            whale_note="Position increased by 4.0%",
            sentiment_note="Neutral",
            trend_note="Mixed trend with RSI 61.0",
            headline_summary="Utility trend intact",
            reported_value=86000000.0,
            market_cap=650000000.0,
            current_price=80.0,
            moving_average_200=79.0,
            rsi_14=61.0,
            score=ScoreBreakdown(
                total_score=65,
                signal_label="Watch",
                institutional_score=0,
                sentiment_score=100,
                technical_score=100,
            ),
            section="watchlist",
        )
    ]

    html = render_email(
        EmailReport(
            picks=picks,
            generated_on="2026-05-11",
            timezone_name="America/New_York",
            investors_scanned=14,
            positions_scanned=32,
            warnings=['MPLXP: quote lookup failed <script>alert(1)</script>'],
        )
    )

    assert "<script>" not in html
    assert "&lt;img" in html
    assert "Informational only" in html
    assert "EVIL&lt;script&gt;" in html
    assert "Institutional Conviction" in html
    assert "$880.0M" in html
    assert "$130.25" in html
    assert "Bullish above 200-day MA" in html
    assert "New position &lt;b&gt;opened&lt;/b&gt;" in html
    assert "Top Picks" in html
    assert "Watchlist" in html
    assert "Run date: 2026-05-11 (America/New_York)" in html
    assert "Investors Scanned" in html
    assert "Positions Scanned" in html
    assert "Warnings and Data Quality Notes" in html
    assert "MPLXP: quote lookup failed &lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "Lead headline" in html
    assert "Reported Value" in html
