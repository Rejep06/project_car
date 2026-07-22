"""Функции для работы с датами в UTC и календарными длительностями."""

from datetime import UTC, datetime

from dateutil.relativedelta import relativedelta


def utcnow() -> datetime:
    """Возвращает текущую timezone-aware дату в UTC."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Нормализует дату к UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def add_duration(value: datetime, amount: int, unit: str) -> datetime:
    """Добавляет календарную длительность к дате."""
    if amount <= 0:
        raise ValueError("Длительность должна быть положительной")
    mapping = {
        "day": {"days": amount},
        "week": {"weeks": amount},
        "month": {"months": amount},
        "year": {"years": amount},
    }
    try:
        return ensure_utc(value) + relativedelta(**mapping[unit])
    except KeyError as exc:
        raise ValueError("Неизвестная единица длительности") from exc


def add_reward_frequency(value: datetime, frequency: str) -> datetime:
    """Добавляет один период выплаты, сохраняя календарную семантику месяца."""
    mapping = {
        "daily": {"days": 1},
        "weekly": {"weeks": 1},
        "monthly": {"months": 1},
    }
    try:
        return ensure_utc(value) + relativedelta(**mapping[frequency])
    except KeyError as exc:
        raise ValueError("Неизвестная частота вознаграждения") from exc
