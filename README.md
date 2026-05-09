# AlphaStream

AlphaStream is a read-only stock intelligence bot that combines 13F filing changes, recent news sentiment, and technical trend checks into a weekly HTML email.

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

## Security notes

- Use `.env` only for local development.
- Use GitHub Actions secrets for scheduled runs.
- Store state files on the `alphastream-state` branch via the workflow checkout.
- Keep the system advisory-only; it does not place trades.
