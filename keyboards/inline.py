"""Inline-клавіатури для пагінації та інших дій."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_history_pagination_keyboard(
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup | None:
    """Повертає inline-клавіатуру для пагінації історії.

    Args:
        current_page: Поточна сторінка (починаючи з 1).
        total_pages: Загальна кількість сторінок.

    Returns:
        InlineKeyboardMarkup або None, якщо пагінація не потрібна.
    """
    if total_pages <= 1:
        return None

    buttons: list[InlineKeyboardButton] = []

    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"history_page:{current_page - 1}",
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="history_page:noop",
        )
    )

    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"history_page:{current_page + 1}",
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[buttons])
