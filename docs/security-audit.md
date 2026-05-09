# AlphaStream Security and Operations Audit

## Secrets and identity

- Local development uses `.env`; scheduled runs must use GitHub Actions encrypted secrets only.
- Scope API keys to single-vendor read access where possible.
- Keep SMTP credentials separate from market-data credentials.
- Rotate secrets on provider compromise, repository access changes, or suspected log exposure.

## Workflow hardening

- `alphastream.yml` runs only on `schedule` and `workflow_dispatch`.
- CI workflows run without production secrets.
- GitHub Actions are pinned to immutable commit SHAs.
- Scheduled workflow writes repository contents only when updating the `alphastream-state` branch.

## Data safety

- Email rendering escapes ticker, company, and headline content before building HTML.
- Logs should avoid printing secrets, raw auth headers, or recipient addresses.
- Missing vendor data is treated as a skip for that ticker, not a full-pipeline crash.

## State management

- Sent-history lives in `state-worktree/state` during execution and is pushed to the `alphastream-state` branch after successful delivery.
- State is updated only after email delivery succeeds.
- Re-runs of the same tickers within 30 days are filtered out before delivery.

## Ongoing checks

- CI runs `pytest`, `pip-audit`, and `detect-secrets`.
- CodeQL scans the Python codebase and workflow files.
- Dependabot watches both Python dependencies and GitHub Actions revisions.
