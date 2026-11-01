"""Сервіс статистики робочого часу."""

from datetime import datetime, timedelta

import pytz

from config import TIMEZONE
from database import get_all_completed_sessions, get_sessions_in_period
from models import WorkSession
from utils.formatting import format_duration

_tz = pytz.timezone(TIMEZONE)


def _start_of_today_utc() -> datetime:
    """Початок поточного дня за місцевим часом, переведений у UTC."""
    now_local = datetime.now(_tz)
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_local.astimezone(pytz.utc)


def _start_of_week_utc() -> datetime:
    """Початок поточного тижня (понеділок) за місцевим часом, переведений у UTC."""
    now_local = datetime.now(_tz)
    # Понеділок = 0, Неділя = 6
    monday = now_local - timedelta(days=now_local.weekday())
    start_local = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    return start_local.astimezone(pytz.utc)


def _start_of_month_utc() -> datetime:
    """Початок поточного місяця за місцевим часом, переведений у UTC."""
    now_local = datetime.now(_tz)
    start_local = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start_local.astimezone(pytz.utc)


def _compute_stats(sessions: list[WorkSession]) -> dict:
    """Розраховує статистику для набору сесій.

    Args:
        sessions: Список завершених робочих змін.

    Returns:
        Словник зі статистикою:
        - count: Кількість змін.
        - total_seconds: Загальна тривалість у секундах.
        - avg_seconds: Середня тривалість у секундах.
        - total_formatted: Форматована загальна тривалість.
        - avg_formatted: Форматована середня тривалість.
    """
    count = len(sessions)
    total_seconds = sum(
        (s.duration_seconds or 0.0) for s in sessions
    )
    avg_seconds = total_seconds / count if count > 0 else 0.0

    return {
        "count": count,
        "total_seconds": total_seconds,
        "avg_seconds": avg_seconds,
        "total_formatted": format_duration(total_seconds),
        "avg_formatted": format_duration(avg_seconds),
    }


async def get_user_statistics(user_id: int) -> dict:
    """Отримує повну статистику користувача.

    Args:
        user_id: ID користувача в базі даних.

    Returns:
        Словник з ключами: today, week, month, total.
        Кожен — словник зі статистикою від _compute_stats.
    """
    now_utc = datetime.now(pytz.utc)
    today_start = _start_of_today_utc()
    week_start = _start_of_week_utc()
    month_start = _start_of_month_utc()

    # Отримуємо дані паралельно (але послідовно для SQLite)
    today_sessions = await get_sessions_in_period(user_id, today_start, now_utc)
    week_sessions = await get_sessions_in_period(user_id, week_start, now_utc)
    month_sessions = await get_sessions_in_period(user_id, month_start, now_utc)
    all_sessions = await get_all_completed_sessions(user_id)

    return {
        "today": _compute_stats(today_sessions),
        "week": _compute_stats(week_sessions),
        "month": _compute_stats(month_sessions),
        "total": _compute_stats(all_sessions),
    }
