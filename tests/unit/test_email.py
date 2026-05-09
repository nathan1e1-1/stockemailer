from alphastream.email.render import render_email
from alphastream.types import RankedPick, ScoreBreakdown


def test_render_email_sanitizes_hostile_content() -> None:
    picks = [
        RankedPick(
            ticker="EVIL<script>",
            company_name='Bad & Co <img src=x onerror="alert(1)">',
            investor_name="Fund",
            strategy_label="AI Tech",
            summary='Contract <b>won</b> & "safe"',
            trend_note="Bullish",
            score=ScoreBreakdown(
                total_score=88,
                signal_label="Strong Signal",
                institutional_score=100,
                sentiment_score=80,
                technical_score=80,
            ),
        )
    ]

    html = render_email(picks)

    assert "<script>" not in html
    assert "&lt;img" in html
    assert "Informational only" in html
    assert "EVIL&lt;script&gt;" in html
