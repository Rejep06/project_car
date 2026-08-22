"""Общие Pydantic-схемы, денежные валидаторы и пагинация."""

import re
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.money import MoneyFormatError, format_amount, parse_amount

T = TypeVar("T")
TXID_PATTERN = re.compile(r"^(?:0x)?[0-9a-fA-F]{64}$")
EVM_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")


class APIModel(BaseModel):
    """Базовая схема с ORM-режимом и строгим заполнением."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True, extra="forbid")


class PaginationResponse(APIModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


class MessageResponse(APIModel):
    message: str


class MoneyResponse(APIModel):
    amount: str
    asset: str = "USDT"

    @classmethod
    def from_atomic(cls, amount_atomic: int, asset: str = "USDT") -> "MoneyResponse":
        return cls(amount=format_amount(amount_atomic), asset=asset)


class IdResponse(APIModel):
    id: UUID


class AmountInput(APIModel):
    amount: str = Field(min_length=1, max_length=100)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        try:
            amount_atomic = parse_amount(value)
        except MoneyFormatError as exc:
            raise ValueError(str(exc)) from exc
        if amount_atomic <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return format_amount(amount_atomic)


class TimestampedResponse(APIModel):
    id: UUID
    created_at: datetime
    updated_at: datetime


def validate_transaction_hash(value: str) -> str:
    """Проверяет хеш транзакции EVM и возвращает канонический вид с 0x."""
    normalized = value.strip().lower()
    if not TXID_PATTERN.fullmatch(normalized):
        raise ValueError("Хеш транзакции должен содержать 64 шестнадцатеричных символа")
    return normalized if normalized.startswith("0x") else f"0x{normalized}"


def validate_txid(value: str) -> str:
    """Обратная совместимость для существующих схем."""
    return validate_transaction_hash(value)


def validate_evm_address(value: str) -> str:
    """Проверяет адрес EVM. Для сопоставления хранится нижний регистр."""
    normalized = value.strip().lower()
    if not EVM_ADDRESS_PATTERN.fullmatch(normalized):
        raise ValueError("Некорректный адрес Ethereum/EVM")
    return normalized


def validate_generic_wallet_address(value: str) -> str:
    """Базовая проверка адреса для сетей без подключённого автопровайдера."""
    normalized = value.strip()
    if not 3 <= len(normalized) <= 256:
        raise ValueError("Адрес должен содержать от 3 до 256 символов")
    if any(char.isspace() for char in normalized):
        raise ValueError("Адрес не должен содержать пробелы")
    return normalized
