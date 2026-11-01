"""Тести для бота обліку робочого часу.

Тестують:
1. Реєстрацію нового користувача.
2. Початок робочої зміни.
3. Повторний початок зміни (захист від дублювання).
4. Завершення робочої зміни.
5. Завершення зміни без початку.
6. Перегляд активної зміни.
7. Перегляд історії (пагінація).
8. Розрахунок статистики.
9. Роботу декількох користувачів одночасно.
10. Збереження активної зміни після перезапуску.
11. Роботу з часовим поясом Europe/Kyiv.
12. Захист особистих даних користувачів.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

import pytz
import pytest
import pytest_asyncio

# Додаємо кореневу директорію проєкту до sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Встановлюємо тестовий BOT_TOKEN до імпорту config
os.environ["BOT_TOKEN"] = "test_token_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

from config import DATABASE_PATH
from models import Base

# ─── Фікстури ────────────────────────────────────────────────────────────────

# Шлях до тестової бази даних
TEST_DB_PATH = DATABASE_PATH.parent / "test_work_time.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session")
def event_loop():
    """Створює єдиний event loop для всіх тестів."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    """Ініціалізує тестову БД перед кожним тестом та очищає після."""
    import database

    # Підміняємо URL на тестову БД
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

    test_engine = create_async_engine(TEST_DB_URL, echo=False)
    test_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    # Підміняємо глобальні об'єкти
    original_engine = database.engine
    original_session = database.async_session

    database.engine = test_engine
    database.async_session = test_session

    # Створюємо таблиці
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Видаляємо таблиці та закриваємо з'єднання
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()

    # Повертаємо оригінальні об'єкти
    database.engine = original_engine
    database.async_session = original_session

    # Видаляємо тестову БД
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


# ─── Тест 1: Реєстрація нового користувача ──────────────────────────────────


@pytest.mark.asyncio
async def test_user_registration():
    """Тест: Реєстрація нового користувача при першому запуску."""
    from database import get_or_create_user, get_user_by_telegram_id

    # Реєструємо нового користувача
    user = await get_or_create_user(
        telegram_id=111111,
        username="test_user",
        first_name="Тест",
        last_name="Тестович",
    )

    assert user is not None
    assert user.telegram_id == 111111
    assert user.username == "test_user"
    assert user.first_name == "Тест"
    assert user.last_name == "Тестович"
    assert user.id is not None

    # Перевіряємо, що користувач існує в БД
    found = await get_user_by_telegram_id(111111)
    assert found is not None
    assert found.telegram_id == 111111


@pytest.mark.asyncio
async def test_user_registration_updates_info():
    """Тест: Повторна реєстрація оновлює інформацію."""
    from database import get_or_create_user

    user1 = await get_or_create_user(
        telegram_id=111112,
        username="old_name",
        first_name="Старе",
    )

    user2 = await get_or_create_user(
        telegram_id=111112,
        username="new_name",
        first_name="Нове",
    )

    assert user1.id == user2.id
    assert user2.username == "new_name"
    assert user2.first_name == "Нове"


# ─── Тест 2: Початок робочої зміни ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_start_work_session():
    """Тест: Початок нової робочої зміни."""
    from database import get_or_create_user, start_work_session, get_active_session
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=222222, username="worker1")
    current_time = now_utc()

    session = await start_work_session(user.id, current_time)

    assert session is not None
    assert session.user_id == user.id
    assert session.start_time is not None
    assert session.end_time is None
    assert session.is_active is True

    # Перевіряємо, що активна зміна знаходиться
    active = await get_active_session(user.id)
    assert active is not None
    assert active.id == session.id


# ─── Тест 3: Повторний початок зміни ────────────────────────────────────────


@pytest.mark.asyncio
async def test_duplicate_start_work_raises_error():
    """Тест: Повторний початок зміни при активній — помилка."""
    from database import get_or_create_user, start_work_session
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=333333, username="worker2")
    current_time = now_utc()

    await start_work_session(user.id, current_time)

    with pytest.raises(ValueError, match="вже є активна"):
        await start_work_session(user.id, current_time)


# ─── Тест 4: Завершення робочої зміни ───────────────────────────────────────


@pytest.mark.asyncio
async def test_end_work_session():
    """Тест: Завершення робочої зміни з розрахунком тривалості."""
    from database import get_or_create_user, start_work_session, end_work_session
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=444444, username="worker3")

    start_time = now_utc()
    await start_work_session(user.id, start_time)

    # Завершуємо зміну через 8.5 годин
    end_time = start_time + timedelta(hours=8, minutes=30)
    session = await end_work_session(user.id, end_time)

    assert session.end_time is not None
    assert session.duration_seconds is not None
    assert session.is_active is False

    # Перевіряємо тривалість (8 год 30 хв = 30600 сек)
    expected_seconds = 8 * 3600 + 30 * 60
    assert abs(session.duration_seconds - expected_seconds) < 1


# ─── Тест 5: Завершення зміни без початку ───────────────────────────────────


@pytest.mark.asyncio
async def test_end_work_without_start_raises_error():
    """Тест: Завершення зміни без активної — помилка."""
    from database import get_or_create_user, end_work_session
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=555555, username="worker4")

    with pytest.raises(ValueError, match="Немає активної"):
        await end_work_session(user.id, now_utc())


# ─── Тест 6: Перегляд активної зміни ────────────────────────────────────────


@pytest.mark.asyncio
async def test_active_session_check():
    """Тест: Перегляд стану активної зміни."""
    from database import get_or_create_user, start_work_session, get_active_session
    from services.time_calculator import calculate_elapsed_seconds
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=666666, username="worker5")

    # Немає активної зміни
    active = await get_active_session(user.id)
    assert active is None

    # Починаємо зміну
    start_time = now_utc()
    await start_work_session(user.id, start_time)

    active = await get_active_session(user.id)
    assert active is not None

    # Перевіряємо розрахунок часу
    later = start_time + timedelta(hours=4, minutes=45)
    elapsed = calculate_elapsed_seconds(active.start_time, later)
    expected = 4 * 3600 + 45 * 60
    assert abs(elapsed - expected) < 1


# ─── Тест 7: Перегляд історії (пагінація) ───────────────────────────────────


@pytest.mark.asyncio
async def test_history_pagination():
    """Тест: Перегляд історії з пагінацією."""
    from database import (
        get_or_create_user,
        start_work_session,
        end_work_session,
        get_user_sessions,
        count_user_sessions,
    )

    user = await get_or_create_user(telegram_id=777777, username="worker6")

    # Створюємо 7 завершених змін
    base_time = datetime(2026, 10, 25, 7, 0, 0, tzinfo=pytz.utc)
    for i in range(7):
        start_time = base_time + timedelta(days=i)
        await start_work_session(user.id, start_time)

        end_time = start_time + timedelta(hours=8)
        await end_work_session(user.id, end_time)

    # Перевіряємо загальну кількість
    total = await count_user_sessions(user.id)
    assert total == 7

    # Перша сторінка (5 записів)
    page1 = await get_user_sessions(user.id, limit=5, offset=0)
    assert len(page1) == 5

    # Друга сторінка (2 записи)
    page2 = await get_user_sessions(user.id, limit=5, offset=5)
    assert len(page2) == 2

    # Записи відсортовані за спаданням (нові першими)
    assert page1[0].start_time > page1[1].start_time


# ─── Тест 8: Розрахунок статистики ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_statistics_calculation():
    """Тест: Розрахунок статистики за різні періоди."""
    from database import get_or_create_user, start_work_session, end_work_session
    from services.statistics_service import get_user_statistics

    user = await get_or_create_user(telegram_id=888888, username="worker7")

    # Створюємо зміну сьогодні
    now = datetime.now(pytz.utc)
    today_start = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if today_start > now:
        today_start -= timedelta(days=1)
    await start_work_session(user.id, today_start)
    await end_work_session(user.id, today_start + timedelta(hours=8, minutes=30))

    stats = await get_user_statistics(user.id)

    # Перевіряємо статистику "Сьогодні"
    assert stats["today"]["count"] >= 1
    assert stats["today"]["total_seconds"] > 0

    # Перевіряємо "Усього"
    assert stats["total"]["count"] >= 1
    assert stats["total"]["total_seconds"] > 0
    assert stats["total"]["avg_seconds"] > 0


# ─── Тест 9: Робота декількох користувачів одночасно ────────────────────────


@pytest.mark.asyncio
async def test_multiple_users_simultaneously():
    """Тест: Кілька користувачів працюють одночасно без конфліктів."""
    from database import (
        get_or_create_user,
        start_work_session,
        end_work_session,
        get_active_session,
    )
    from utils.timezone import now_utc

    # Створюємо 3 користувачів
    user1 = await get_or_create_user(telegram_id=900001, username="multi_user1")
    user2 = await get_or_create_user(telegram_id=900002, username="multi_user2")
    user3 = await get_or_create_user(telegram_id=900003, username="multi_user3")

    current = now_utc()

    # Всі починають роботу
    await start_work_session(user1.id, current)
    await start_work_session(user2.id, current + timedelta(minutes=5))
    await start_work_session(user3.id, current + timedelta(minutes=10))

    # Перевіряємо, що кожен має свою активну зміну
    active1 = await get_active_session(user1.id)
    active2 = await get_active_session(user2.id)
    active3 = await get_active_session(user3.id)

    assert active1 is not None
    assert active2 is not None
    assert active3 is not None
    assert active1.id != active2.id != active3.id

    # User2 завершує роботу, інші продовжують
    await end_work_session(user2.id, current + timedelta(hours=8))

    assert await get_active_session(user1.id) is not None
    assert await get_active_session(user2.id) is None
    assert await get_active_session(user3.id) is not None


# ─── Тест 10: Збереження активної зміни після перезапуску ────────────────────


@pytest.mark.asyncio
async def test_session_survives_restart():
    """Тест: Активна зміна зберігається після 'перезапуску' бота."""
    from database import (
        get_or_create_user,
        start_work_session,
        get_active_session,
    )
    from utils.timezone import now_utc

    user = await get_or_create_user(telegram_id=101010, username="restart_user")
    start_time = now_utc()

    # Починаємо зміну
    session = await start_work_session(user.id, start_time)
    session_id = session.id

    # Імітуємо "перезапуск" — нове підключення до БД
    active = await get_active_session(user.id)
    assert active is not None
    assert active.id == session_id
    assert active.end_time is None


# ─── Тест 11: Робота з часовим поясом Europe/Kyiv ───────────────────────────


@pytest.mark.asyncio
async def test_timezone_handling():
    """Тест: Коректна робота з часовим поясом Europe/Kyiv."""
    from utils.timezone import now_utc, utc_to_local, local_now
    from utils.formatting import format_date, format_time

    utc_now = now_utc()
    local = utc_to_local(utc_now)
    local_current = local_now()

    # UTC та локальний час мають відрізнятися (Kyiv = UTC+2 або UTC+3)
    utc_offset = local.utcoffset()
    assert utc_offset is not None
    offset_hours = utc_offset.total_seconds() / 3600
    assert offset_hours in (2, 3)  # Залежить від DST

    # Перевіряємо форматування
    date_str = format_date(utc_now)
    assert "." in date_str  # DD.MM.YYYY
    parts = date_str.split(".")
    assert len(parts) == 3

    time_str = format_time(utc_now)
    assert ":" in time_str  # HH:MM


# ─── Тест 12: Захист особистих даних ────────────────────────────────────────


@pytest.mark.asyncio
async def test_data_isolation():
    """Тест: Користувач не може переглядати чужі дані."""
    from database import (
        get_or_create_user,
        start_work_session,
        end_work_session,
        get_user_sessions,
        get_active_session,
    )
    from utils.timezone import now_utc

    user_a = await get_or_create_user(telegram_id=120001, username="user_a")
    user_b = await get_or_create_user(telegram_id=120002, username="user_b")

    # User A створює зміну
    start_time = now_utc()
    await start_work_session(user_a.id, start_time)
    await end_work_session(user_a.id, start_time + timedelta(hours=8))

    # User B не повинен бачити зміни User A
    sessions_b = await get_user_sessions(user_b.id)
    assert len(sessions_b) == 0

    active_b = await get_active_session(user_b.id)
    assert active_b is None

    # User A бачить свої зміни
    sessions_a = await get_user_sessions(user_a.id)
    assert len(sessions_a) == 1


# ─── Додаткові тести ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_duration_formatting():
    """Тест: Форматування тривалості."""
    from utils.formatting import format_duration

    assert format_duration(0) == "0 хв"
    assert format_duration(60) == "1 хв"
    assert format_duration(3600) == "1 год 0 хв"
    assert format_duration(3660) == "1 год 1 хв"
    assert format_duration(30600) == "8 год 30 хв"
    assert format_duration(7200) == "2 год 0 хв"
    assert format_duration(-100) == "0 хв"


@pytest.mark.asyncio
async def test_overnight_shift():
    """Тест: Зміна, що переходить через північ."""
    from database import get_or_create_user, start_work_session, end_work_session

    user = await get_or_create_user(telegram_id=130001, username="night_worker")

    # Починаємо ввечері, завершуємо вранці
    start_time = datetime(2026, 10, 31, 20, 0, 0, tzinfo=pytz.utc)
    await start_work_session(user.id, start_time)

    end_time = datetime(2026, 11, 1, 6, 0, 0, tzinfo=pytz.utc)
    session = await end_work_session(user.id, end_time)

    # 10 годин
    assert abs(session.duration_seconds - 36000) < 1


@pytest.mark.asyncio
async def test_time_calculator():
    """Тест: Сервіс розрахунку часу."""
    from services.time_calculator import calculate_duration_seconds, calculate_elapsed_seconds

    start = datetime(2026, 11, 1, 9, 0, 0, tzinfo=pytz.utc)
    end = datetime(2026, 11, 1, 17, 30, 0, tzinfo=pytz.utc)

    duration = calculate_duration_seconds(start, end)
    assert duration == 30600  # 8h 30min

    elapsed = calculate_elapsed_seconds(start, end)
    assert elapsed == 30600

    # Від'ємна тривалість повертає 0
    negative = calculate_duration_seconds(end, start)
    assert negative == 0.0


@pytest.mark.asyncio
async def test_inline_keyboard_pagination():
    """Тест: Inline-клавіатура пагінації."""
    from keyboards.inline import get_history_pagination_keyboard

    # Одна сторінка — клавіатура не потрібна
    kb = get_history_pagination_keyboard(1, 1)
    assert kb is None

    # Перша з трьох сторінок
    kb = get_history_pagination_keyboard(1, 3)
    assert kb is not None
    buttons = kb.inline_keyboard[0]
    assert len(buttons) == 2  # Лічильник + Вперед
    assert "1/3" in buttons[0].text
    assert "Вперед" in buttons[1].text

    # Середня сторінка
    kb = get_history_pagination_keyboard(2, 3)
    buttons = kb.inline_keyboard[0]
    assert len(buttons) == 3  # Назад + Лічильник + Вперед

    # Остання сторінка
    kb = get_history_pagination_keyboard(3, 3)
    buttons = kb.inline_keyboard[0]
    assert len(buttons) == 2  # Назад + Лічильник
    assert "Назад" in buttons[0].text
