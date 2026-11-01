"""Обробник команди /start та реєстрація користувача."""

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database import get_or_create_user
from keyboards.main_menu import get_main_menu

logger = logging.getLogger(__name__)
router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обробник команди /start — привітання та реєстрація."""
    if message.from_user is None:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    name = user.first_name or user.username or "користувач"
    text = (
        f"👋 Привіт, <b>{name}</b>!\n\n"
        "Я — бот для обліку робочого часу.\n\n"
        "Використовуйте меню нижче для керування робочими змінами:\n\n"
        "🟢 <b>Почати роботу</b> — розпочати робочу зміну\n"
        "🔴 <b>Завершити роботу</b> — завершити робочу зміну\n"
        "⏱ <b>Поточна зміна</b> — подивитись поточний статус\n"
        "📅 <b>Історія роботи</b> — переглянути минулі зміни\n"
        "📊 <b>Моя статистика</b> — ваша статистика\n"
        "ℹ️ <b>Допомога</b> — інструкція з користування"
    )

    await message.answer(text, reply_markup=get_main_menu(), parse_mode="HTML")
    logger.info("Користувач %s (%d) запустив бота.", name, message.from_user.id)
