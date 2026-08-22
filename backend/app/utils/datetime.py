"""Функции для работы с датами в UTC и календарными длительностями."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dateutil.relativedelta import relativedelta


WEEKDAY_LABELS = (
    "понедельник",
    "вторник",
    "среду",
    "четверг",
    "пятницу",
    "субботу",
    "воскресенье",
)


@dataclass(frozen=True)
class WithdrawalWindow:
    is_open: bool
    timezone: str
    local_now: datetime
    next_open_at: datetime | None
    weekday_label: str


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


def get_withdrawal_window(
    *,
    timezone_name: str,
    allowed_weekday: int,
    now: datetime | None = None,
) -> WithdrawalWindow:
    """Возвращает доступность подачи заявки в локальном времени компании."""
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Неизвестный часовой пояс компании") from exc

    local_now = ensure_utc(now or utcnow()).astimezone(timezone)
    if allowed_weekday == -1:
        return WithdrawalWindow(
            is_open=True,
            timezone=timezone_name,
            local_now=local_now,
            next_open_at=None,
            weekday_label="любой день",
        )

    is_open = local_now.weekday() == allowed_weekday
    if is_open:
        next_open_at = None
    else:
        days_ahead = (allowed_weekday - local_now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        next_date = (local_now + timedelta(days=days_ahead)).date()
        next_local = datetime.combine(next_date, time.min, tzinfo=timezone)
        next_open_at = next_local.astimezone(UTC)

    return WithdrawalWindow(
        is_open=is_open,
        timezone=timezone_name,
        local_now=local_now,
        next_open_at=next_open_at,
        weekday_label=WEEKDAY_LABELS[allowed_weekday],
    )
