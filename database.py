"""Модуль для роботи з базою даних (async SQLAlchemy + aiosqlite)."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import DATABASE_URL
from models import Base, User, WorkSession

logger = logging.getLogger(__name__)


# Створення асинхронного двигуна та фабрики сесій
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Ініціалізація бази даних — створення всіх таблиць."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База даних ініціалізована.")


async def close_db() -> None:
    """Закриття з'єднання з базою даних."""
    await engine.dispose()
    logger.info("З'єднання з базою даних закрито.")


# ─── Користувачі ────────────────────────────────────────────────────────────


async def get_or_create_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """Отримує існуючого або створює нового користувача.

    Args:
        telegram_id: Telegram ID користувача.
        username: Username у Telegram.
        first_name: Ім'я користувача.
        last_name: Прізвище користувача.

    Returns:
        Об'єкт User.
    """
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info("Створено нового користувача: %s (tg_id=%d)", username, telegram_id)
        else:
            # Оновлюємо ім'я/username, якщо змінилися
            updated = False
            if user.username != username:
                user.username = username
                updated = True
            if user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if user.last_name != last_name:
                user.last_name = last_name
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)

        return user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    """Отримує користувача за Telegram ID.

    Args:
        telegram_id: Telegram ID користувача.

    Returns:
        Об'єкт User або None.
    """
    async with async_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# ─── Робочі зміни ───────────────────────────────────────────────────────────


async def get_active_session(user_id: int) -> WorkSession | None:
    """Отримує активну (незавершену) робочу зміну користувача.

    Args:
        user_id: ID користувача у базі даних.

    Returns:
        Об'єкт WorkSession або None.
    """
    async with async_session() as session:
        stmt = (
            select(WorkSession)
            .where(
                WorkSession.user_id == user_id,
                WorkSession.end_time.is_(None),
            )
            .order_by(WorkSession.start_time.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def start_work_session(user_id: int, start_time: datetime) -> WorkSession:
    """Створює нову робочу зміну.

    Args:
        user_id: ID користувача у базі даних.
        start_time: Час початку роботи (UTC).

    Returns:
        Створений об'єкт WorkSession.

    Raises:
        ValueError: Якщо у користувача вже є активна зміна.
    """
    # Перевірка на наявність активної зміни
    active = await get_active_session(user_id)
    if active is not None:
        raise ValueError("У користувача вже є активна робоча зміна.")

    async with async_session() as session:
        work_session = WorkSession(
            user_id=user_id,
            start_time=start_time,
        )
        session.add(work_session)
        await session.commit()
        await session.refresh(work_session)
        logger.info("Розпочато робочу зміну: user_id=%d", user_id)
        return work_session


async def end_work_session(
    user_id: int, end_time: datetime
) -> WorkSession:
    """Завершує активну робочу зміну.

    Args:
        user_id: ID користувача у базі даних.
        end_time: Час завершення роботи (UTC).

    Returns:
        Оновлений об'єкт WorkSession.

    Raises:
        ValueError: Якщо немає активної зміни або тривалість від'ємна.
    """
    active = await get_active_session(user_id)
    if active is None:
        raise ValueError("Немає активної робочої зміни.")

    duration = (end_time - active.start_time).total_seconds()
    if duration < 0:
        raise ValueError("Час завершення не може бути раніше за час початку.")

    async with async_session() as session:
        stmt = select(WorkSession).where(WorkSession.id == active.id)
        result = await session.execute(stmt)
        work_session = result.scalar_one()

        work_session.end_time = end_time
        work_session.duration_seconds = duration

        await session.commit()
        await session.refresh(work_session)
        logger.info(
            "Завершено робочу зміну: user_id=%d, тривалість=%.0f сек",
            user_id,
            duration,
        )
        return work_session


async def get_user_sessions(
    user_id: int,
    limit: int | None = None,
    offset: int = 0,
) -> list[WorkSession]:
    """Отримує завершені робочі зміни користувача з пагінацією.

    Args:
        user_id: ID користувача.
        limit: Максимальна кількість записів.
        offset: Зміщення від початку.

    Returns:
        Список об'єктів WorkSession.
    """
    async with async_session() as session:
        stmt = (
            select(WorkSession)
            .where(
                WorkSession.user_id == user_id,
                WorkSession.end_time.isnot(None),
            )
            .order_by(WorkSession.start_time.desc())
            .offset(offset)
        )
        if limit is not None:
            stmt = stmt.limit(limit)

        result = await session.execute(stmt)
        return list(result.scalars().all())


async def count_user_sessions(user_id: int) -> int:
    """Рахує кількість завершених робочих змін користувача.

    Args:
        user_id: ID користувача.

    Returns:
        Кількість завершених змін.
    """
    from sqlalchemy import func as sa_func

    async with async_session() as session:
        stmt = (
            select(sa_func.count(WorkSession.id))
            .where(
                WorkSession.user_id == user_id,
                WorkSession.end_time.isnot(None),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one()


async def get_sessions_in_period(
    user_id: int,
    start: datetime,
    end: datetime,
) -> list[WorkSession]:
    """Отримує завершені робочі зміни користувача за період.

    Args:
        user_id: ID користувача.
        start: Початок періоду (UTC).
        end: Кінець періоду (UTC).

    Returns:
        Список об'єктів WorkSession.
    """
    async with async_session() as session:
        stmt = (
            select(WorkSession)
            .where(
                WorkSession.user_id == user_id,
                WorkSession.end_time.isnot(None),
                WorkSession.start_time >= start,
                WorkSession.start_time < end,
            )
            .order_by(WorkSession.start_time.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_all_completed_sessions(user_id: int) -> list[WorkSession]:
    """Отримує всі завершені робочі зміни користувача.

    Args:
        user_id: ID користувача.

    Returns:
        Список об'єктів WorkSession.
    """
    async with async_session() as session:
        stmt = (
            select(WorkSession)
            .where(
                WorkSession.user_id == user_id,
                WorkSession.end_time.isnot(None),
            )
            .order_by(WorkSession.start_time.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
