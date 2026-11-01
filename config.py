"""Конфігурація бота для обліку робочого часу."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Завантажуємо змінні середовища з .env файлу
load_dotenv()

# Telegram Bot Token
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN не знайдено! "
        "Створіть файл .env та додайте BOT_TOKEN=ваш_токен"
    )

# Шляхи
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "data"
DATABASE_PATH: Path = DATA_DIR / "work_time.db"

# База даних
DATABASE_URL: str = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# Часовий пояс
TIMEZONE: str = "Europe/Kyiv"

# Пагінація
HISTORY_PAGE_SIZE: int = 5
