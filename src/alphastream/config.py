from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    investors: list[dict[str, str]]
    sector_map: dict[str, dict[str, object]]
    weights: dict[str, float]
    thresholds: dict[str, float | int]
    market_cap_min: float
    dedupe_days: int
    target_total_picks: int
    max_top_picks: int
    top_pick_min_score: int
    watchlist_min_score: int
    report_timezone: str
    filing_provider: str
    fixture_file: Path
    sec_user_agent: str
    email_provider: str
    email_from: str
    email_to: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    fmp_api_key: str
    finnhub_api_key: str
    state_dir: Path


def _load_yaml(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text())
    return data if isinstance(data, dict) else {}


def load_config(config_dir: str | Path = "config") -> AppConfig:
    load_dotenv()
    config_root = Path(config_dir)
    investors = _load_yaml(config_root / "investors.yaml").get("investors", [])
    sectors = _load_yaml(config_root / "sectors.yaml").get("strategies", {})
    scoring = _load_yaml(config_root / "scoring.yaml").get("scoring", {})
    weights = scoring.get("weights", {})
    thresholds = scoring.get("thresholds", {})
    selection = scoring.get("selection", {})
    email_from = os.environ.get("ALPHASTREAM_EMAIL_FROM", "")
    return AppConfig(
        investors=list(investors),
        sector_map=dict(sectors),
        weights={key: float(value) for key, value in dict(weights).items()},
        thresholds={key: value for key, value in dict(thresholds).items()},
        market_cap_min=float(scoring.get("market_cap_min", 500_000_000)),
        dedupe_days=int(selection.get("dedupe_days", 7)),
        target_total_picks=int(selection.get("target_total_picks", 8)),
        max_top_picks=int(selection.get("max_top_picks", 5)),
        top_pick_min_score=int(selection.get("top_pick_min_score", thresholds.get("strong_signal", 80))),
        watchlist_min_score=int(selection.get("watchlist_min_score", 50)),
        report_timezone=os.environ.get("ALPHASTREAM_REPORT_TIMEZONE", str(scoring.get("report_timezone", "America/New_York"))),
        filing_provider=os.environ.get("ALPHASTREAM_FILING_PROVIDER", "sec"),
        fixture_file=Path(os.environ.get("ALPHASTREAM_FIXTURE_FILE", "fixtures/demo_filings.json")),
        sec_user_agent=os.environ.get(
            "ALPHASTREAM_SEC_USER_AGENT",
            f"AlphaStreamBot/1.0 ({email_from or 'alphastream@example.com'})",
        ),
        email_provider=os.environ.get("ALPHASTREAM_EMAIL_PROVIDER", "smtp"),
        email_from=email_from,
        email_to=os.environ.get("ALPHASTREAM_EMAIL_TO", ""),
        smtp_host=os.environ.get("ALPHASTREAM_SMTP_HOST", ""),
        smtp_port=int(os.environ.get("ALPHASTREAM_SMTP_PORT", "587")),
        smtp_username=os.environ.get("ALPHASTREAM_SMTP_USERNAME", ""),
        smtp_password=os.environ.get("ALPHASTREAM_SMTP_PASSWORD", ""),
        fmp_api_key=os.environ.get("ALPHASTREAM_FMP_API_KEY", ""),
        finnhub_api_key=os.environ.get("ALPHASTREAM_FINNHUB_API_KEY", ""),
        state_dir=Path(os.environ.get("ALPHASTREAM_STATE_DIR", "state-worktree/state")),
    )
