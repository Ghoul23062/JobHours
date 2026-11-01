"""Точка входу — запуск Telegram-бота для обліку робочого часу."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import close_db, init_db
from handlers import help, history, start, statistics, work

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Головна асинхронна функція запуску бота."""
    logger.info("Ініціалізація бота...")

    # Ініціалізація бази даних
    await init_db()

    # Створення бота та диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Реєстрація роутерів (порядок має значення!)
    dp.include_routers(
        start.router,
        work.router,
        history.router,
        statistics.router,
        help.router,
    )

    logger.info("Бот запущено. Очікування повідомлень...")

    try:
        # Видаляємо вебхуки та запускаємо polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_db()
        await bot.session.close()
        logger.info("Бот зупинено.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено користувачем (Ctrl+C).")
