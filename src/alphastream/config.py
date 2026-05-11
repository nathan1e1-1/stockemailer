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


class ConfigError(ValueError):
    pass


def _load_yaml(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text())
    return data if isinstance(data, dict) else {}


def _get_env(name: str, default: str = "") -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped if stripped else default


def _get_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ConfigError(f"{name} must be an integer, got {raw!r}.") from error


def _validate_config(config: AppConfig) -> None:
    if config.email_provider not in {"smtp", "console"}:
        raise ConfigError(f"Unsupported ALPHASTREAM_EMAIL_PROVIDER {config.email_provider!r}.")
    if config.filing_provider not in {"sec", "fmp", "fixture"}:
        raise ConfigError(f"Unsupported ALPHASTREAM_FILING_PROVIDER {config.filing_provider!r}.")
    if config.filing_provider == "fixture" and not config.fixture_file.exists():
        raise ConfigError(f"Fixture filing file does not exist: {config.fixture_file}")

    missing: list[str] = []
    if not config.finnhub_api_key:
        missing.append("ALPHASTREAM_FINNHUB_API_KEY")
    if config.email_provider == "smtp":
        for name, value in [
            ("ALPHASTREAM_EMAIL_FROM", config.email_from),
            ("ALPHASTREAM_EMAIL_TO", config.email_to),
            ("ALPHASTREAM_SMTP_HOST", config.smtp_host),
            ("ALPHASTREAM_SMTP_USERNAME", config.smtp_username),
            ("ALPHASTREAM_SMTP_PASSWORD", config.smtp_password),
        ]:
            if not value:
                missing.append(name)
    if config.filing_provider == "fmp" and not config.fmp_api_key:
        missing.append("ALPHASTREAM_FMP_API_KEY")

    if missing:
        required = ", ".join(sorted(set(missing)))
        raise ConfigError(
            f"Missing required configuration: {required}. "
            "Set these values in your local .env file or GitHub Actions secrets."
        )


def load_config(config_dir: str | Path = "config") -> AppConfig:
    load_dotenv()
    config_root = Path(config_dir)
    investors = _load_yaml(config_root / "investors.yaml").get("investors", [])
    sectors = _load_yaml(config_root / "sectors.yaml").get("strategies", {})
    scoring = _load_yaml(config_root / "scoring.yaml").get("scoring", {})
    weights = scoring.get("weights", {})
    thresholds = scoring.get("thresholds", {})
    selection = scoring.get("selection", {})
    email_from = _get_env("ALPHASTREAM_EMAIL_FROM", "")
    config = AppConfig(
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
        report_timezone=_get_env("ALPHASTREAM_REPORT_TIMEZONE", str(scoring.get("report_timezone", "America/New_York"))),
        filing_provider=_get_env("ALPHASTREAM_FILING_PROVIDER", "sec"),
        fixture_file=Path(_get_env("ALPHASTREAM_FIXTURE_FILE", "fixtures/demo_filings.json")),
        sec_user_agent=_get_env(
            "ALPHASTREAM_SEC_USER_AGENT",
            f"AlphaStreamBot/1.0 ({email_from or 'alphastream@example.com'})",
        ),
        email_provider=_get_env("ALPHASTREAM_EMAIL_PROVIDER", "smtp"),
        email_from=email_from,
        email_to=_get_env("ALPHASTREAM_EMAIL_TO", ""),
        smtp_host=_get_env("ALPHASTREAM_SMTP_HOST", ""),
        smtp_port=_get_int_env("ALPHASTREAM_SMTP_PORT", 587),
        smtp_username=_get_env("ALPHASTREAM_SMTP_USERNAME", ""),
        smtp_password=_get_env("ALPHASTREAM_SMTP_PASSWORD", ""),
        fmp_api_key=_get_env("ALPHASTREAM_FMP_API_KEY", ""),
        finnhub_api_key=_get_env("ALPHASTREAM_FINNHUB_API_KEY", ""),
        state_dir=Path(_get_env("ALPHASTREAM_STATE_DIR", "state-worktree/state")),
    )
    _validate_config(config)
    return config
