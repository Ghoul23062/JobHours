"""Сервіс для розрахунку часу."""

from datetime import datetime


def calculate_duration_seconds(start: datetime, end: datetime) -> float:
    """Розраховує тривалість між двома моментами часу в секундах.

    Args:
        start: Час початку.
        end: Час завершення.

    Returns:
        Тривалість у секундах (не менше 0).
    """
    duration = (end - start).total_seconds()
    return max(0.0, duration)


def calculate_elapsed_seconds(start: datetime, now: datetime) -> float:
    """Розраховує скільки секунд пройшло від початку до поточного моменту.

    Args:
        start: Час початку.
        now: Поточний час.

    Returns:
        Кількість секунд (не менше 0).
    """
    elapsed = (now - start).total_seconds()
    return max(0.0, elapsed)
