from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def should_send_daily_email(now: datetime, tz_name: str = "America/New_York", target_hour: int = 7) -> bool:
    localized = now.astimezone(ZoneInfo(tz_name))
    return localized.hour >= target_hour


def should_send_weekday_email(now: datetime, tz_name: str = "America/New_York", target_hour: int = 7) -> bool:
    return should_send_daily_email(now=now, tz_name=tz_name, target_hour=target_hour)
