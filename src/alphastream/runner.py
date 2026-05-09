from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from alphastream.email.render import render_email
from alphastream.pipeline import classify_strategy, filter_candidates
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
    dedupe_days: int = 30

    def run(self, today: date | None = None) -> RunResult:
        today = today or date.today()
        candidate_signals: list[CandidateSignal] = []
        errors: list[str] = []
        since = (today - timedelta(days=120)).isoformat()
        investor_ids = [str(investor["id"]) for investor in self.investors]
        positions = self.filing_provider.fetch_positions(since=since, investor_ids=investor_ids)
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
                errors.append(f"{filing.ticker}: {error}")
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
        picks = sorted((self._build_pick(candidate, scoring_engine) for candidate in filtered), key=lambda pick: pick.score.total_score, reverse=True)
        report = EmailReport(picks=picks, generated_on=today.isoformat())
        delivery = self.email_sender.send(report)
        if delivery.success:
            self.state_store.record_success([pick.ticker for pick in picks], today=today)
            return RunResult(sent_count=len(picks), skipped_count=0, errors=errors)
        return RunResult(sent_count=0, skipped_count=len(picks), errors=errors + ([delivery.error] if delivery.error else []))

    def _build_pick(self, candidate: CandidateSignal, scoring_engine: ScoringEngine) -> RankedPick:
        score = scoring_engine.score(candidate)
        summary = candidate.headlines[0].title if candidate.headlines else "No recent news available."
        trend_note = (
            "Bullish" if candidate.market.current_price > candidate.market.moving_average_200 and candidate.market.rsi_14 < float(self.thresholds.get("overbought_rsi", 70.0))
            else "Mixed"
        )
        return RankedPick(
            ticker=candidate.filing.ticker,
            company_name=candidate.market.company_name or candidate.filing.company_name,
            investor_name=candidate.filing.investor_name,
            strategy_label=candidate.strategy_label,
            summary=summary,
            trend_note=trend_note,
            score=score,
        )
