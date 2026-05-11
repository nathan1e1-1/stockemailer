# AlphaStream

AlphaStream is a read-only stock intelligence bot that combines 13F filing changes, recent news sentiment, and technical trend checks into a weekday HTML email.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
cp .env.example .env
pytest
alphastream --config-dir config
```

## Immediate local email test without paid 13F access

Set `ALPHASTREAM_FILING_PROVIDER=fixture` in `.env` and leave `ALPHASTREAM_FIXTURE_FILE=fixtures/demo_filings.json` to use the bundled sample filing. This keeps the real Finnhub, market-data, scoring, and SMTP path, but skips the paid 13F fetch.

## Production filing source

The live automation defaults to `ALPHASTREAM_FILING_PROVIDER=sec`, which reads recent 13F filings from SEC sources and resolves tickers from the SEC company ticker directory. Set `ALPHASTREAM_SEC_USER_AGENT` to a descriptive contact string before using the SEC path.

## Security notes

- Use `.env` only for local development.
- Use GitHub Actions secrets for scheduled runs.
- Store state files on the `alphastream-state` branch via the workflow checkout.
- Keep the system advisory-only; it does not place trades.
