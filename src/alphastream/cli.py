from __future__ import annotations

import argparse
from pathlib import Path

from alphastream.config import load_config
from alphastream.email.senders import ConsoleEmailSender, SMTPEmailSender
from alphastream.providers.filings import FMPFilingProvider
from alphastream.providers.market import YFinanceMarketDataProvider
from alphastream.providers.news import FinnhubNewsProvider
from alphastream.runner import AlphaStreamRunner
from alphastream.state import FileStateStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AlphaStream weekly pipeline.")
    parser.add_argument("--config-dir", default="config", help="Directory that contains AlphaStream YAML config files.")
    parser.add_argument("--dry-run", action="store_true", help="Render report without sending live email.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config_dir)
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
        filing_provider=FMPFilingProvider(api_key=config.fmp_api_key),
        news_provider=FinnhubNewsProvider(api_key=config.finnhub_api_key),
        market_provider=YFinanceMarketDataProvider(),
        state_store=FileStateStore(Path(config.state_dir)),
        email_sender=email_sender,
        investors=config.investors,
        sector_map=config.sector_map,
        weights=config.weights,
        thresholds=config.thresholds,
        market_cap_min=config.market_cap_min,
    )
    result = runner.run()
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
