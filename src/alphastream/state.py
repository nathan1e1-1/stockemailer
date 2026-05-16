from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class FileStateStore:
    base_dir: Path

    def __post_init__(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sent_path = self.base_dir / "sent_tickers.json"
        self.last_run_path = self.base_dir / "last_run.json"

    def get_recently_sent(self) -> dict[str, date]:
        if not self.sent_path.exists():
            return {}
        payload = json.loads(self.sent_path.read_text())
        return {ticker: date.fromisoformat(sent_on) for ticker, sent_on in payload.items()}

    def get_last_successful_run(self) -> date | None:
        if not self.last_run_path.exists():
            return None
        payload = json.loads(self.last_run_path.read_text())
        last_run = payload.get("last_successful_run")
        return date.fromisoformat(last_run) if last_run else None

    def was_sent_recently(self, ticker: str, within_days: int, today: date) -> bool:
        last_sent = self.get_recently_sent().get(ticker.upper())
        return last_sent is not None and (today - last_sent).days < within_days

    def record_success(self, tickers: list[str], today: date) -> None:
        payload = {ticker.upper(): sent_on.isoformat() for ticker, sent_on in self.get_recently_sent().items()}
        for ticker in tickers:
            payload[ticker.upper()] = today.isoformat()
        self.sent_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        self.last_run_path.write_text(json.dumps({"last_successful_run": today.isoformat()}, indent=2))
