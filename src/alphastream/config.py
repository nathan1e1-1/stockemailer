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
    return AppConfig(
        investors=list(investors),
        sector_map=dict(sectors),
        weights={key: float(value) for key, value in dict(weights).items()},
        thresholds={key: value for key, value in dict(thresholds).items()},
        market_cap_min=float(scoring.get("market_cap_min", 500_000_000)),
        email_provider=os.environ.get("ALPHASTREAM_EMAIL_PROVIDER", "smtp"),
        email_from=os.environ.get("ALPHASTREAM_EMAIL_FROM", ""),
        email_to=os.environ.get("ALPHASTREAM_EMAIL_TO", ""),
        smtp_host=os.environ.get("ALPHASTREAM_SMTP_HOST", ""),
        smtp_port=int(os.environ.get("ALPHASTREAM_SMTP_PORT", "587")),
        smtp_username=os.environ.get("ALPHASTREAM_SMTP_USERNAME", ""),
        smtp_password=os.environ.get("ALPHASTREAM_SMTP_PASSWORD", ""),
        fmp_api_key=os.environ.get("ALPHASTREAM_FMP_API_KEY", ""),
        finnhub_api_key=os.environ.get("ALPHASTREAM_FINNHUB_API_KEY", ""),
        state_dir=Path(os.environ.get("ALPHASTREAM_STATE_DIR", "state-worktree/state")),
    )
