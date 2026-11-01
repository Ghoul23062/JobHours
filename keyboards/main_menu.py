"""Головне меню бота — ReplyKeyboardMarkup."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

# Текстові константи кнопок головного меню
BTN_START_WORK = "🟢 Почати роботу"
BTN_STOP_WORK = "🔴 Завершити роботу"
BTN_CURRENT_SHIFT = "⏱ Поточна зміна"
BTN_HISTORY = "📅 Історія роботи"
BTN_STATISTICS = "📊 Моя статистика"
BTN_HELP = "ℹ️ Допомога"


def get_main_menu() -> ReplyKeyboardMarkup:
    """Повертає клавіатуру головного меню."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BTN_START_WORK),
                KeyboardButton(text=BTN_STOP_WORK),
            ],
            [
                KeyboardButton(text=BTN_CURRENT_SHIFT),
                KeyboardButton(text=BTN_HISTORY),
            ],
            [
                KeyboardButton(text=BTN_STATISTICS),
                KeyboardButton(text=BTN_HELP),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
    return keyboard
