from datetime import date
from pathlib import Path

from alphastream.state import FileStateStore


def test_state_store_tracks_recent_send_window(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path)
    store.record_success(["NVDA"], today=date(2026, 5, 8))

    assert store.was_sent_recently("NVDA", within_days=7, today=date(2026, 5, 8)) is True
    assert store.was_sent_recently("NVDA", within_days=7, today=date(2026, 5, 14)) is True
    assert store.was_sent_recently("NVDA", within_days=7, today=date(2026, 5, 15)) is False


def test_state_store_persists_last_run(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path)
    store.record_success(["MSFT"], today=date(2026, 5, 8))

    assert (tmp_path / "sent_tickers.json").exists()
    assert (tmp_path / "last_run.json").exists()


def test_state_store_reads_last_successful_run(tmp_path: Path) -> None:
    store = FileStateStore(tmp_path)
    store.record_success(["MSFT"], today=date(2026, 5, 8))

    assert store.get_last_successful_run() == date(2026, 5, 8)
