from __future__ import annotations

from dataclasses import dataclass

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from alphastream.types import CandidateSignal, ScoreBreakdown


@dataclass
class ScoringEngine:
    weights: dict[str, float]
    overbought_rsi: float
    strong_signal_threshold: int

    def __post_init__(self) -> None:
        self.analyzer = SentimentIntensityAnalyzer()

    def score(self, candidate: CandidateSignal) -> ScoreBreakdown:
        institutional_score = 100 if (
            candidate.filing.is_new_position or candidate.filing.stake_increase_pct >= 10.0
        ) else 0
        sentiment_score = self._score_sentiment(candidate.headlines)
        technical_score = 100 if (
            candidate.market.current_price > candidate.market.moving_average_200
            and candidate.market.rsi_14 < self.overbought_rsi
        ) else 0
        weighted_total = (
            institutional_score * self.weights["institutional"]
            + sentiment_score * self.weights["sentiment"]
            + technical_score * self.weights["technical"]
        )
        total_score = int(round(weighted_total))
        signal_label = "Strong Signal" if total_score >= self.strong_signal_threshold else "Watch"
        return ScoreBreakdown(
            total_score=total_score,
            signal_label=signal_label,
            institutional_score=institutional_score,
            sentiment_score=sentiment_score,
            technical_score=technical_score,
        )

    def _score_sentiment(self, headlines) -> int:
        if not headlines:
            return 50
        combined = " ".join(filter(None, [f"{headline.title} {headline.summary}".strip() for headline in headlines]))
        compound = self.analyzer.polarity_scores(combined)["compound"]
        if compound > 0.2:
            return 100
        if compound < -0.2:
            return 0
        lowered = combined.lower()
        positive_markers = ("beat", "beats", "contract", "signed", "expands", "growth", "upgrade")
        negative_markers = ("lawsuit", "downgrade", "miss", "cuts", "fraud", "probe")
        if any(marker in lowered for marker in positive_markers):
            return 100
        if any(marker in lowered for marker in negative_markers):
            return 0
        return 50
