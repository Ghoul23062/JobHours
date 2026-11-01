"""Обробник історії робочих змін з пагінацією."""

import logging
import math

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import HISTORY_PAGE_SIZE
from database import count_user_sessions, get_or_create_user, get_user_sessions
from keyboards.inline import get_history_pagination_keyboard
from keyboards.main_menu import BTN_HISTORY
from utils.formatting import format_date, format_duration, format_time

logger = logging.getLogger(__name__)
router = Router(name="history")


def _build_history_text(
    sessions: list, current_page: int, total_pages: int
) -> str:
    """Формує текст сторінки історії."""
    if not sessions:
        return (
            "📅 <b>Історія роботи</b>\n\n"
            "У вас поки немає завершених робочих змін."
        )

    lines = [f"📅 <b>Історія роботи</b> (стор. {current_page}/{total_pages})\n"]

    for session in sessions:
        lines.append(
            f"📅 {format_date(session.start_time)}\n"
            f"🕒 {format_time(session.start_time)} — "
            f"{format_time(session.end_time)}\n"
            f"⏱ {format_duration(session.duration_seconds)}\n"
        )

    return "\n".join(lines)


@router.message(F.text == BTN_HISTORY)
async def handle_history(message: Message) -> None:
    """Обробник кнопки '📅 Історія роботи' — перша сторінка."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    total = await count_user_sessions(user.id)
    total_pages = max(1, math.ceil(total / HISTORY_PAGE_SIZE))
    current_page = 1

    sessions = await get_user_sessions(
        user.id, limit=HISTORY_PAGE_SIZE, offset=0
    )

    text = _build_history_text(sessions, current_page, total_pages)
    keyboard = get_history_pagination_keyboard(current_page, total_pages)

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("history_page:"))
async def handle_history_page(callback: CallbackQuery) -> None:
    """Обробник inline-кнопок пагінації історії."""
    if callback.message is None or callback.from_user is None:
        return

    page_str = callback.data.split(":")[1]
    if page_str == "noop":
        await callback.answer()
        return

    try:
        current_page = int(page_str)
    except ValueError:
        await callback.answer("⚠️ Помилка навігації.")
        return

    if current_page < 1:
        current_page = 1

    user = await get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
    )

    total = await count_user_sessions(user.id)
    total_pages = max(1, math.ceil(total / HISTORY_PAGE_SIZE))

    if current_page > total_pages:
        current_page = total_pages

    offset = (current_page - 1) * HISTORY_PAGE_SIZE
    sessions = await get_user_sessions(
        user.id, limit=HISTORY_PAGE_SIZE, offset=offset
    )

    text = _build_history_text(sessions, current_page, total_pages)
    keyboard = get_history_pagination_keyboard(current_page, total_pages)

    await callback.message.edit_text(
        text, reply_markup=keyboard, parse_mode="HTML"
    )
    await callback.answer()
