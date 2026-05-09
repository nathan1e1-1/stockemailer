from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FilingPosition:
    ticker: str
    company_name: str
    investor_id: str
    investor_name: str
    is_new_position: bool
    stake_increase_pct: float
    reported_value: float
    sector: str


@dataclass(frozen=True)
class Headline:
    title: str
    summary: str
    published_at: str


@dataclass(frozen=True)
class MarketSnapshot:
    ticker: str
    company_name: str
    market_cap: float
    sector: str
    current_price: float
    moving_average_200: float
    rsi_14: float


@dataclass(frozen=True)
class CandidateSignal:
    filing: FilingPosition
    headlines: list[Headline]
    market: MarketSnapshot
    strategy_label: str


@dataclass(frozen=True)
class ScoreBreakdown:
    total_score: int
    signal_label: str
    institutional_score: int
    sentiment_score: int
    technical_score: int


@dataclass(frozen=True)
class RankedPick:
    ticker: str
    company_name: str
    investor_name: str
    strategy_label: str
    summary: str
    trend_note: str
    score: ScoreBreakdown


@dataclass(frozen=True)
class EmailReport:
    picks: list[RankedPick]
    generated_on: str


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    provider_name: str
    message_id: str | None
    error: str | None


@dataclass(frozen=True)
class RunResult:
    sent_count: int
    skipped_count: int
    errors: list[str] = field(default_factory=list)
