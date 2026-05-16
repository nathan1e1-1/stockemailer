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
    snapshots = {
        "NVDA": MarketSnapshot(
            ticker="NVDA",
            company_name="NVIDIA Corporation",
            market_cap=1_000_000_000.0,
            sector="Technology",
            current_price=120.0,
            moving_average_200=100.0,
            rsi_14=55.0,
        ),
        "VST": MarketSnapshot(
            ticker="VST",
            company_name="Vistra Corp.",
            market_cap=900_000_000.0,
            sector="Utilities",
            current_price=85.0,
            moving_average_200=82.0,
            rsi_14=62.0,
        ),
        "UNH": MarketSnapshot(
            ticker="UNH",
            company_name="UnitedHealth Group",
            market_cap=800_000_000.0,
            sector="Healthcare",
            current_price=510.0,
            moving_average_200=500.0,
            rsi_14=58.0,
        ),
    }

    def fetch_snapshot(self, ticker):
        return self.snapshots[ticker]


class StubStateStore:
    def __init__(self):
        self.recorded = []
        self.last_successful_run = None

    def get_recently_sent(self):
        return {}

    def get_last_successful_run(self):
        return self.last_successful_run

    def record_success(self, tickers, today):
        self.recorded.append((tuple(tickers), today))
        self.last_successful_run = today


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
    assert email_sender.sent_reports[0].picks[0].whale_note == "New position opened"
    assert "Bullish above 200-day MA" in email_sender.sent_reports[0].picks[0].trend_note
    assert state_store.recorded == [(("NVDA",), date(2026, 5, 8))]
    assert result.warnings == []


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


class MultiStubFilingProvider:
    def fetch_positions(self, since, investor_ids):
        return [
            FilingPosition(
                ticker="NVDA",
                company_name="NVIDIA Corporation",
                investor_id="1067983",
                investor_name="Berkshire Hathaway",
                is_new_position=True,
                stake_increase_pct=12.5,
                reported_value=1_000_000.0,
                sector="Technology",
            ),
            FilingPosition(
                ticker="VST",
                company_name="Vistra Corp.",
                investor_id="1336528",
                investor_name="Pershing Square",
                is_new_position=False,
                stake_increase_pct=14.0,
                reported_value=850_000.0,
                sector="Utilities",
            ),
            FilingPosition(
                ticker="UNH",
                company_name="UnitedHealth Group",
                investor_id="1029160",
                investor_name="Soros Fund Management",
                is_new_position=False,
                stake_increase_pct=5.0,
                reported_value=650_000.0,
                sector="Healthcare",
            ),
        ]


class MultiStubNewsProvider:
    headlines = {
        "NVDA": [Headline(title="AI infrastructure demand rises", summary="strong outlook", published_at="2026-05-08T10:00:00Z")],
        "VST": [Headline(title="Utility demand rises with grid expansion", summary="steady outlook", published_at="2026-05-08T10:00:00Z")],
        "UNH": [Headline(title="Healthcare contract expansion stabilizes outlook", summary="improved outlook", published_at="2026-05-08T10:00:00Z")],
    }

    def fetch_headlines(self, ticker, lookback_hours=48):
        return self.headlines[ticker]


def test_runner_partitions_top_picks_and_watchlist() -> None:
    state_store = StubStateStore()
    email_sender = StubEmailSender()
    runner = AlphaStreamRunner(
        filing_provider=MultiStubFilingProvider(),
        news_provider=MultiStubNewsProvider(),
        market_provider=StubMarketProvider(),
        state_store=state_store,
        email_sender=email_sender,
        investors=[
            {"id": "1067983", "name": "Berkshire Hathaway"},
            {"id": "1336528", "name": "Pershing Square"},
            {"id": "1029160", "name": "Soros Fund Management"},
        ],
        sector_map={
            "ai_tech": {"label": "AI Tech", "sectors": ["Technology"], "keywords": ["ai", "infrastructure"]},
            "energy_play": {"label": "Energy Play", "sectors": ["Utilities"], "keywords": ["utility", "grid"]},
            "value_rotation": {"label": "Value Rotation", "sectors": ["Healthcare"], "keywords": ["healthcare"]},
        },
        weights={"institutional": 0.4, "sentiment": 0.3, "technical": 0.3},
        thresholds={"lookback_hours": 48, "overbought_rsi": 70.0, "strong_signal": 80},
        market_cap_min=500_000_000.0,
        target_total_picks=3,
        max_top_picks=2,
        top_pick_min_score=80,
        watchlist_min_score=50,
    )

    result = runner.run(today=date(2026, 5, 8))

    assert result.sent_count == 3
    assert [(pick.ticker, pick.section) for pick in email_sender.sent_reports[0].picks] == [
        ("NVDA", "top_pick"),
        ("VST", "top_pick"),
        ("UNH", "watchlist"),
    ]


def test_runner_skips_duplicate_send_when_state_already_recorded_for_today() -> None:
    state_store = StubStateStore()
    state_store.last_successful_run = date(2026, 5, 8)
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

    assert result.sent_count == 0
    assert result.skipped_count == 0
    assert email_sender.sent_reports == []
