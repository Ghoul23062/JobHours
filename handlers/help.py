"""Обробник команди допомоги."""

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main_menu import BTN_HELP

logger = logging.getLogger(__name__)
router = Router(name="help")

HELP_TEXT = (
    "ℹ️ <b>ДОПОМОГА</b>\n\n"
    "Цей бот допомагає вести облік робочого часу.\n\n"
    "<b>Як користуватися:</b>\n\n"
    "1️⃣ <b>🟢 Почати роботу</b>\n"
    "Натисніть на початку робочого дня. Бот зафіксує час початку.\n\n"
    "2️⃣ <b>🔴 Завершити роботу</b>\n"
    "Натисніть наприкінці робочого дня. Бот зафіксує час завершення "
    "та покаже скільки годин ви відпрацювали.\n\n"
    "3️⃣ <b>⏱ Поточна зміна</b>\n"
    "Подивіться скільки часу ви вже працюєте.\n\n"
    "4️⃣ <b>📅 Історія роботи</b>\n"
    "Перегляньте минулі робочі зміни з пагінацією.\n\n"
    "5️⃣ <b>📊 Моя статистика</b>\n"
    "Подивіться статистику за сьогодні, тиждень, місяць та весь час.\n\n"
    "<b>Важливо:</b>\n"
    "• Не можна почати нову зміну, якщо попередня не завершена.\n"
    "• Часовий пояс: Europe/Kyiv.\n"
    "• Якщо бот перезавантажився, ваша активна зміна збережеться.\n\n"
    "Якщо меню зникло — введіть /start"
)


@router.message(F.text == BTN_HELP)
async def handle_help_button(message: Message) -> None:
    """Обробник кнопки 'ℹ️ Допомога'."""
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("help"))
async def handle_help_command(message: Message) -> None:
    """Обробник команди /help."""
    await message.answer(HELP_TEXT, parse_mode="HTML")
