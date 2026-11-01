"""SQLAlchemy моделі для бота обліку робочого часу."""

from datetime import datetime

import pytz
from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    event,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовий клас для всіх моделей."""

    pass


class User(Base):
    """Модель користувача."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Зв'язок з робочими сесіями
    work_sessions: Mapped[list["WorkSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, "
            f"username={self.username!r})>"
        )


class WorkSession(Base):
    """Модель робочої зміни."""

    __tablename__ = "work_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Зв'язок з користувачем
    user: Mapped["User"] = relationship(back_populates="work_sessions")

    # Індекси для оптимізації запитів
    __table_args__ = (
        Index("ix_work_sessions_user_id_start_time", "user_id", "start_time"),
        Index("ix_work_sessions_user_id_end_time", "user_id", "end_time"),
    )

    @property
    def is_active(self) -> bool:
        """Чи є зміна активною (не завершеною)."""
        return self.end_time is None

    def __repr__(self) -> str:
        return (
            f"<WorkSession(id={self.id}, user_id={self.user_id}, "
            f"start={self.start_time}, end={self.end_time})>"
        )


# ─── Нормалізація timezone після завантаження з SQLite ────────────────────────


def _ensure_utc(dt: datetime | None) -> datetime | None:
    """Додає UTC tzinfo до naive datetime (SQLite не зберігає tz)."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.utc)
    return dt


@event.listens_for(WorkSession, "load")
def _normalize_work_session_tz(target: WorkSession, _context: object) -> None:
    """Нормалізує timezone полів datetime після завантаження з БД."""
    target.start_time = _ensure_utc(target.start_time)
    target.end_time = _ensure_utc(target.end_time)
    target.created_at = _ensure_utc(target.created_at)


@event.listens_for(User, "load")
def _normalize_user_tz(target: User, _context: object) -> None:
    """Нормалізує timezone полів datetime після завантаження з БД."""
    target.created_at = _ensure_utc(target.created_at)
