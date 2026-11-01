"""Утиліти для форматування тексту та часу."""

from datetime import datetime

from utils.timezone import utc_to_local


def format_duration(total_seconds: int | float) -> str:
    """Форматує тривалість у секундах як 'X год Y хв'.

    Args:
        total_seconds: Кількість секунд.

    Returns:
        Рядок виду '8 год 30 хв' або '0 хв' для нульової тривалості.
    """
    if total_seconds < 0:
        total_seconds = 0

    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours > 0 and minutes > 0:
        return f"{hours} год {minutes} хв"
    elif hours > 0:
        return f"{hours} год 0 хв"
    else:
        return f"{minutes} хв"


def format_date(dt: datetime) -> str:
    """Форматує datetime у рядок дати 'DD.MM.YYYY' у локальному часовому поясі."""
    local_dt = utc_to_local(dt)
    return local_dt.strftime("%d.%m.%Y")


def format_time(dt: datetime) -> str:
    """Форматує datetime у рядок часу 'HH:MM' у локальному часовому поясі."""
    local_dt = utc_to_local(dt)
    return local_dt.strftime("%H:%M")


def format_datetime(dt: datetime) -> str:
    """Форматує datetime у рядок 'DD.MM.YYYY HH:MM' у локальному часовому поясі."""
    local_dt = utc_to_local(dt)
    return local_dt.strftime("%d.%m.%Y %H:%M")
