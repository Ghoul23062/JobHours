"""Утиліти для роботи з часовими поясами."""

from datetime import datetime

import pytz

from config import TIMEZONE

_tz = pytz.timezone(TIMEZONE)


def now_utc() -> datetime:
    """Повертає поточний час у UTC (aware)."""
    return datetime.now(tz=pytz.utc)


def utc_to_local(dt: datetime) -> datetime:
    """Конвертує UTC datetime у локальний часовий пояс Europe/Kyiv."""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(_tz)


def local_now() -> datetime:
    """Повертає поточний локальний час у Europe/Kyiv."""
    return now_utc().astimezone(_tz)
