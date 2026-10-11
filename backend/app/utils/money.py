"""Безопасное преобразование денежных сумм USDT без использования float."""

from decimal import Decimal, InvalidOperation

ATOMIC_FACTOR = 1_000_000
MAX_ATOMIC = 9_223_372_036_854_775_807
_DECIMAL_QUANT = Decimal("0.000001")


class MoneyFormatError(ValueError):
    """Входная сумма имеет недопустимый формат или точность."""


def parse_amount(value: str) -> int:
    """Преобразует строку USDT в целое количество atomic units.

    Поддерживается не более шести знаков после запятой. Округление не
    выполняется: лишняя точность считается ошибкой.
    """
    if not isinstance(value, str):
        raise MoneyFormatError("Сумма должна быть строкой")
    stripped = value.strip()
    if not stripped:
        raise MoneyFormatError("Сумма не может быть пустой")
    try:
        decimal_value = Decimal(stripped)
    except InvalidOperation as exc:
        raise MoneyFormatError("Некорректный формат суммы") from exc
    if not decimal_value.is_finite():
        raise MoneyFormatError("Сумма должна быть конечным числом")
    try:
        quantized = decimal_value.quantize(_DECIMAL_QUANT)
    except InvalidOperation as exc:
        raise MoneyFormatError("Слишком большое значение суммы") from exc
    if quantized != decimal_value:
        raise MoneyFormatError("Допустимо не более 6 знаков после запятой")
    atomic = int(quantized * ATOMIC_FACTOR)
    if abs(atomic) > MAX_ATOMIC:
        raise MoneyFormatError("Сумма превышает диапазон PostgreSQL BIGINT")
    return atomic


def format_amount(value: int) -> str:
    """Преобразует atomic units в строку с шестью знаками после запятой."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("Atomic amount должен быть целым числом")
    sign = "-" if value < 0 else ""
    absolute = abs(value)
    whole, fraction = divmod(absolute, ATOMIC_FACTOR)
    return f"{sign}{whole}.{fraction:06d}"


def percentage_fee(amount_atomic: int, percent: int) -> int:
    """Процент от суммы с округлением half-up до одного atomic unit.

    1 atomic unit = 0.000001 USDT. Расчёт целочисленный: например,
    10% от 20.000005 USDT округляются с 2.0000005 до 2.000001 USDT.
    """
    if not isinstance(amount_atomic, int) or isinstance(amount_atomic, bool) or amount_atomic < 0:
        raise ValueError("Сумма должна быть целым неотрицательным количеством atomic units")
    if not isinstance(percent, int) or isinstance(percent, bool) or not 0 <= percent <= 100:
        raise ValueError("Процент комиссии должен быть целым числом от 0 до 100")
    return (amount_atomic * percent + 50) // 100
