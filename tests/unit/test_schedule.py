from datetime import datetime
from zoneinfo import ZoneInfo

from alphastream.schedule import should_send_weekday_email


def test_schedule_allows_weekday_7am_new_york() -> None:
    now = datetime(2026, 5, 11, 7, 0, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_weekday_email(now) is True


def test_schedule_allows_delayed_weekday_run_after_target_hour() -> None:
    delayed = datetime(2026, 5, 11, 9, 1, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_weekday_email(delayed) is True


def test_schedule_blocks_weekend_and_run_before_target_hour() -> None:
    saturday = datetime(2026, 5, 9, 7, 0, tzinfo=ZoneInfo("America/New_York"))
    too_early = datetime(2026, 5, 11, 6, 59, tzinfo=ZoneInfo("America/New_York"))

    assert should_send_weekday_email(saturday) is False
    assert should_send_weekday_email(too_early) is False
