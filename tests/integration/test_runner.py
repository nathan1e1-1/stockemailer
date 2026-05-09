from datetime import date

from alphastream.runner import AlphaStreamRunner
from alphastream.types import (
    CandidateSignal,
    DeliveryResult,
    FilingPosition,
    Headline,
    MarketSnapshot,
)


class StubFilingProvider:
    def fetch_positions(self, since, investor_ids):
        return [
            FilingPosition(
                ticker="NVDA",
                company_name="NVIDIA Corporation",
                investor_id="berkshire-hathaway",
                investor_name="Berkshire Hathaway",
                is_new_position=True,
                stake_increase_pct=12.5,
                reported_value=1_000_000.0,
                sector="Technology",
            )
        ]


class StubNewsProvider:
    def fetch_headlines(self, ticker, lookback_hours=48):
        return [Headline(title="AI infrastructure demand rises", summary="strong outlook", published_at="2026-05-08T10:00:00Z")]


class StubMarketProvider:
    def fetch_snapshot(self, ticker):
        return MarketSnapshot(
            ticker=ticker,
            company_name="NVIDIA Corporation",
            market_cap=1_000_000_000.0,
            sector="Technology",
            current_price=120.0,
            moving_average_200=100.0,
            rsi_14=55.0,
        )


class StubStateStore:
    def __init__(self):
        self.recorded = []

    def get_recently_sent(self):
        return {}

    def record_success(self, tickers, today):
        self.recorded.append((tuple(tickers), today))


class StubEmailSender:
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.sent_reports = []

    def send(self, report):
        self.sent_reports.append(report)
        return DeliveryResult(success=self.should_succeed, provider_name="stub", message_id="123", error=None if self.should_succeed else "boom")


def test_runner_sends_ranked_picks_and_updates_state_on_success() -> None:
    state_store = StubStateStore()
    email_sender = StubEmailSender()
    runner = AlphaStreamRunner(
        filing_provider=StubFilingProvider(),
        news_provider=StubNewsProvider(),
        market_provider=StubMarketProvider(),
        state_store=state_store,
        email_sender=email_sender,
        investors=[{"id": "berkshire-hathaway", "name": "Berkshire Hathaway"}],
        sector_map={
            "ai_tech": {"label": "AI Tech", "sectors": ["Technology"], "keywords": ["ai", "infrastructure"]},
        },
        weights={"institutional": 0.4, "sentiment": 0.3, "technical": 0.3},
        thresholds={"lookback_hours": 48, "overbought_rsi": 70.0, "strong_signal": 80},
        market_cap_min=500_000_000.0,
    )

    result = runner.run(today=date(2026, 5, 8))

    assert result.sent_count == 1
    assert result.skipped_count == 0
    assert email_sender.sent_reports[0].picks[0].ticker == "NVDA"
    assert state_store.recorded == [(("NVDA",), date(2026, 5, 8))]


def test_runner_does_not_update_state_when_delivery_fails() -> None:
    state_store = StubStateStore()
    email_sender = StubEmailSender(should_succeed=False)
    runner = AlphaStreamRunner(
        filing_provider=StubFilingProvider(),
        news_provider=StubNewsProvider(),
        market_provider=StubMarketProvider(),
        state_store=state_store,
        email_sender=email_sender,
        investors=[{"id": "berkshire-hathaway", "name": "Berkshire Hathaway"}],
        sector_map={
            "ai_tech": {"label": "AI Tech", "sectors": ["Technology"], "keywords": ["ai", "infrastructure"]},
        },
        weights={"institutional": 0.4, "sentiment": 0.3, "technical": 0.3},
        thresholds={"lookback_hours": 48, "overbought_rsi": 70.0, "strong_signal": 80},
        market_cap_min=500_000_000.0,
    )

    result = runner.run(today=date(2026, 5, 8))

    assert result.sent_count == 0
    assert result.skipped_count == 1
    assert state_store.recorded == []
