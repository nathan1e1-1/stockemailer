from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from alphastream.pipeline import classify_strategy, filter_candidates, partition_ranked_picks
from alphastream.scoring import ScoringEngine
from alphastream.types import CandidateSignal, EmailReport, RankedPick, RunResult


@dataclass
class AlphaStreamRunner:
    filing_provider: object
    news_provider: object
    market_provider: object
    state_store: object
    email_sender: object
    investors: list[dict[str, str]]
    sector_map: dict[str, dict[str, object]]
    weights: dict[str, float]
    thresholds: dict[str, float | int]
    market_cap_min: float
    dedupe_days: int = 7
    target_total_picks: int = 8
    max_top_picks: int = 5
    top_pick_min_score: int = 80
    watchlist_min_score: int = 50
    report_timezone: str = "America/New_York"

    def run(self, today: date | None = None) -> RunResult:
        today = today or date.today()
        if getattr(self.state_store, "get_last_successful_run", lambda: None)() == today:
            return RunResult(sent_count=0, skipped_count=0, errors=[], warnings=["A successful report was already sent today."])
        candidate_signals: list[CandidateSignal] = []
        errors: list[str] = []
        warnings: list[str] = []
        since = (today - timedelta(days=120)).isoformat()
        investor_ids = [str(investor["id"]) for investor in self.investors]
        positions = self.filing_provider.fetch_positions(since=since, investor_ids=investor_ids)
        warnings.extend(getattr(self.filing_provider, "last_errors", []))
        for filing in positions:
            try:
                headlines = self.news_provider.fetch_headlines(
                    filing.ticker,
                    lookback_hours=int(self.thresholds.get("lookback_hours", 48)),
                )
                market = self.market_provider.fetch_snapshot(filing.ticker)
                descriptive_text = " ".join(
                    [filing.company_name, filing.sector] + [f"{headline.title} {headline.summary}".strip() for headline in headlines]
                )
                strategy = classify_strategy(market.sector or filing.sector, descriptive_text, self.sector_map)
                if not strategy:
                    continue
                candidate_signals.append(
                    CandidateSignal(
                        filing=filing,
                        headlines=headlines,
                        market=market,
                        strategy_label=strategy,
                    )
                )
            except Exception as error:  # pragma: no cover - exercised in live runs
                warnings.append(f"{filing.ticker}: {error}")
        recently_sent = self.state_store.get_recently_sent()
        filtered = filter_candidates(
            candidate_signals,
            market_cap_min=self.market_cap_min,
            recently_sent=recently_sent,
            today=today,
            dedupe_days=self.dedupe_days,
        )
        scoring_engine = ScoringEngine(
            weights=self.weights,
            overbought_rsi=float(self.thresholds.get("overbought_rsi", 70.0)),
            strong_signal_threshold=int(self.thresholds.get("strong_signal", 80)),
        )
        ranked = sorted((self._build_pick(candidate, scoring_engine) for candidate in filtered), key=lambda pick: pick.score.total_score, reverse=True)
        picks = partition_ranked_picks(
            ranked,
            top_pick_min_score=self.top_pick_min_score,
            watchlist_min_score=self.watchlist_min_score,
            max_top_picks=self.max_top_picks,
            target_total_picks=self.target_total_picks,
        )
        report = EmailReport(picks=picks, generated_on=today.isoformat(), timezone_name=self.report_timezone)
        delivery = self.email_sender.send(report)
        if delivery.success:
            self.state_store.record_success([pick.ticker for pick in picks], today=today)
            return RunResult(sent_count=len(picks), skipped_count=0, errors=errors, warnings=warnings)
        return RunResult(
            sent_count=0,
            skipped_count=len(picks),
            errors=errors + ([delivery.error] if delivery.error else []),
            warnings=warnings,
        )

    def _build_pick(self, candidate: CandidateSignal, scoring_engine: ScoringEngine) -> RankedPick:
        score = scoring_engine.score(candidate)
        headline = candidate.headlines[0] if candidate.headlines else None
        whale_note = (
            "New position opened"
            if candidate.filing.is_new_position
            else f"Position increased by {candidate.filing.stake_increase_pct:.1f}%"
        )
        sentiment_note = headline.title if headline else "No recent news available."
        trend_note = (
            f"Bullish above 200-day MA with RSI {candidate.market.rsi_14:.1f}"
            if candidate.market.current_price > candidate.market.moving_average_200 and candidate.market.rsi_14 < float(self.thresholds.get("overbought_rsi", 70.0))
            else f"Mixed trend with RSI {candidate.market.rsi_14:.1f}"
        )
        return RankedPick(
            ticker=candidate.filing.ticker,
            company_name=candidate.market.company_name or candidate.filing.company_name,
            investor_name=candidate.filing.investor_name,
            strategy_label=candidate.strategy_label,
            whale_note=whale_note,
            sentiment_note=sentiment_note,
            trend_note=trend_note,
            market_cap=candidate.market.market_cap,
            current_price=candidate.market.current_price,
            moving_average_200=candidate.market.moving_average_200,
            rsi_14=candidate.market.rsi_14,
            score=score,
        )
