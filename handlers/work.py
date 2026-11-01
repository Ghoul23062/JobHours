"""Обробники робочих змін: початок, завершення, поточна зміна."""

import logging

from aiogram import F, Router
from aiogram.types import Message

from database import (
    end_work_session,
    get_active_session,
    get_or_create_user,
    start_work_session,
)
from keyboards.main_menu import BTN_CURRENT_SHIFT, BTN_START_WORK, BTN_STOP_WORK
from services.time_calculator import calculate_elapsed_seconds
from utils.formatting import format_date, format_duration, format_time
from utils.timezone import now_utc

logger = logging.getLogger(__name__)
router = Router(name="work")


@router.message(F.text == BTN_START_WORK)
async def handle_start_work(message: Message) -> None:
    """Обробник кнопки '🟢 Почати роботу'."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Перевіряємо, чи немає активної зміни
    active = await get_active_session(user.id)
    if active is not None:
        elapsed = calculate_elapsed_seconds(active.start_time, now_utc())
        text = (
            "⚠️ У вас вже є активна робоча зміна!\n\n"
            f"📅 Дата: {format_date(active.start_time)}\n"
            f"🕒 Початок роботи: {format_time(active.start_time)}\n"
            f"⏱ Відпрацьовано: {format_duration(elapsed)}\n\n"
            "Спочатку завершіть поточну зміну."
        )
        await message.answer(text, parse_mode="HTML")
        return

    # Створюємо нову зміну
    current_time = now_utc()
    session = await start_work_session(user.id, current_time)

    text = (
        "🟢 <b>Робочий день розпочато!</b>\n\n"
        f"📅 Дата: {format_date(session.start_time)}\n"
        f"🕒 Початок роботи: {format_time(session.start_time)}\n\n"
        "Гарного робочого дня! 💪"
    )
    await message.answer(text, parse_mode="HTML")
    logger.info("Користувач %d розпочав зміну.", message.from_user.id)


@router.message(F.text == BTN_STOP_WORK)
async def handle_stop_work(message: Message) -> None:
    """Обробник кнопки '🔴 Завершити роботу'."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    # Перевіряємо наявність активної зміни
    active = await get_active_session(user.id)
    if active is None:
        await message.answer(
            "⚠️ У вас немає активної робочої зміни.\n\n"
            "Натисніть «🟢 Почати роботу», щоб розпочати."
        )
        return

    # Завершуємо зміну
    current_time = now_utc()
    session = await end_work_session(user.id, current_time)

    text = (
        "🔴 <b>Робочий день завершено!</b>\n\n"
        f"📅 Дата: {format_date(session.start_time)}\n"
        f"🕒 Початок: {format_time(session.start_time)}\n"
        f"🕒 Завершення: {format_time(session.end_time)}\n\n"
        f"⏱ Відпрацьовано: <b>{format_duration(session.duration_seconds)}</b>\n\n"
        "Гарного відпочинку! 🌙"
    )
    await message.answer(text, parse_mode="HTML")
    logger.info("Користувач %d завершив зміну.", message.from_user.id)


@router.message(F.text == BTN_CURRENT_SHIFT)
async def handle_current_shift(message: Message) -> None:
    """Обробник кнопки '⏱ Поточна зміна'."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    active = await get_active_session(user.id)
    if active is None:
        await message.answer(
            "💤 Ви зараз не працюєте.\n\n"
            "Натисніть «🟢 Почати роботу», щоб розпочати робочу зміну."
        )
        return

    current_time = now_utc()
    elapsed = calculate_elapsed_seconds(active.start_time, current_time)

    text = (
        "🟢 <b>Ви зараз працюєте.</b>\n\n"
        f"📅 Дата: {format_date(active.start_time)}\n"
        f"🕒 Початок: {format_time(active.start_time)}\n"
        f"🕒 Поточний час: {format_time(current_time)}\n\n"
        f"⏱ Відпрацьовано: <b>{format_duration(elapsed)}</b>"
    )
    await message.answer(text, parse_mode="HTML")
