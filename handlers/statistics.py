"""Обробник статистики робочого часу."""

import logging

from aiogram import F, Router
from aiogram.types import Message

from database import get_active_session, get_or_create_user
from keyboards.main_menu import BTN_STATISTICS
from services.statistics_service import get_user_statistics
from services.time_calculator import calculate_elapsed_seconds
from utils.formatting import format_duration
from utils.timezone import now_utc

logger = logging.getLogger(__name__)
router = Router(name="statistics")


@router.message(F.text == BTN_STATISTICS)
async def handle_statistics(message: Message) -> None:
    """Обробник кнопки '📊 Моя статистика'."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    stats = await get_user_statistics(user.id)

    # Перевіряємо, чи є активна зміна, і додаємо її до "Сьогодні"
    active = await get_active_session(user.id)
    active_info = ""
    if active is not None:
        elapsed = calculate_elapsed_seconds(active.start_time, now_utc())
        active_info = f"\n🟢 Поточна зміна: {format_duration(elapsed)} (у процесі)"

    lines = ["📊 <b>МОЯ СТАТИСТИКА</b>\n"]

    # Сьогодні
    today = stats["today"]
    lines.append("<b>📅 Сьогодні:</b>")
    if today["count"] > 0 or active_info:
        if today["count"] > 0:
            lines.append(f"  Завершено змін: {today['count']}")
            lines.append(f"  ⏱ {today['total_formatted']}")
            lines.append(f"  Середня зміна: {today['avg_formatted']}")
        if active_info:
            lines.append(active_info)
    else:
        lines.append("  Змін не було")
    lines.append("")

    # Цей тиждень
    week = stats["week"]
    lines.append("<b>📅 Цей тиждень:</b>")
    if week["count"] > 0:
        lines.append(f"  Завершено змін: {week['count']}")
        lines.append(f"  ⏱ {week['total_formatted']}")
        lines.append(f"  Середня зміна: {week['avg_formatted']}")
    else:
        lines.append("  Змін не було")
    lines.append("")

    # Цей місяць
    month = stats["month"]
    lines.append("<b>📅 Цей місяць:</b>")
    if month["count"] > 0:
        lines.append(f"  Завершено змін: {month['count']}")
        lines.append(f"  ⏱ {month['total_formatted']}")
        lines.append(f"  Середня зміна: {month['avg_formatted']}")
    else:
        lines.append("  Змін не було")
    lines.append("")

    # Усього
    total = stats["total"]
    lines.append("<b>📅 Усього:</b>")
    if total["count"] > 0:
        lines.append(f"  Завершено змін: {total['count']}")
        lines.append(f"  ⏱ {total['total_formatted']}")
        lines.append(f"  Середня зміна: {total['avg_formatted']}")
    else:
        lines.append("  Змін не було")

    text = "\n".join(lines)
    await message.answer(text, parse_mode="HTML")
