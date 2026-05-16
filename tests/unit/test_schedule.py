from datetime import datetime
from zoneinfo import ZoneInfo

from alphastream.schedule import should_send_daily_email


def test_schedule_allows_daily_7am_new_york() -> None:
    now = datetime(2026, 5, 11, 7, 0, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_daily_email(now) is True


def test_schedule_allows_delayed_daily_run_after_target_hour() -> None:
    delayed = datetime(2026, 5, 11, 9, 1, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_daily_email(delayed) is True


def test_schedule_allows_weekend_after_target_hour() -> None:
    saturday = datetime(2026, 5, 9, 7, 0, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_daily_email(saturday) is True


def test_schedule_blocks_run_before_target_hour() -> None:
    too_early = datetime(2026, 5, 11, 6, 59, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_daily_email(too_early) is False
