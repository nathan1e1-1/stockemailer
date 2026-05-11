from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alphastream.config import ConfigError, load_config
from alphastream.email.senders import ConsoleEmailSender, SMTPEmailSender
from alphastream.providers.fixture_filings import LocalFixtureFilingProvider
from alphastream.providers.filings import FMPFilingProvider
from alphastream.providers.market import YFinanceMarketDataProvider
from alphastream.providers.news import FinnhubNewsProvider
from alphastream.providers.sec_filings import SECFilingProvider
from alphastream.runner import AlphaStreamRunner
from alphastream.state import FileStateStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AlphaStream weekly pipeline.")
    parser.add_argument("--config-dir", default="config", help="Directory that contains AlphaStream YAML config files.")
    parser.add_argument("--dry-run", action="store_true", help="Render report without sending live email.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        config = load_config(args.config_dir)
    except ConfigError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1
    filing_provider = (
        LocalFixtureFilingProvider(Path(config.fixture_file))
        if config.filing_provider == "fixture"
        else (
            SECFilingProvider(user_agent=config.sec_user_agent)
            if config.filing_provider == "sec"
            else FMPFilingProvider(api_key=config.fmp_api_key)
        )
    )
    email_sender = (
        ConsoleEmailSender()
        if args.dry_run or config.email_provider == "console"
        else SMTPEmailSender(
            host=config.smtp_host,
            port=config.smtp_port,
            username=config.smtp_username,
            password=config.smtp_password,
            from_address=config.email_from,
            to_address=config.email_to,
        )
    )
    runner = AlphaStreamRunner(
        filing_provider=filing_provider,
        news_provider=FinnhubNewsProvider(api_key=config.finnhub_api_key),
        market_provider=YFinanceMarketDataProvider(),
        state_store=FileStateStore(Path(config.state_dir)),
        email_sender=email_sender,
        investors=config.investors,
        sector_map=config.sector_map,
        weights=config.weights,
        thresholds=config.thresholds,
        market_cap_min=config.market_cap_min,
        dedupe_days=config.dedupe_days,
        target_total_picks=config.target_total_picks,
        max_top_picks=config.max_top_picks,
        top_pick_min_score=config.top_pick_min_score,
        watchlist_min_score=config.watchlist_min_score,
        report_timezone=config.report_timezone,
    )
    result = runner.run()
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
