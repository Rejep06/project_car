"""Общие Pydantic-схемы, денежные валидаторы и пагинация."""

import re
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.money import MoneyFormatError, format_amount, parse_amount

T = TypeVar("T")
TXID_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")
TRON_ADDRESS_PATTERN = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")


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


def validate_txid(value: str) -> str:
    normalized = value.strip().lower()
    if not TXID_PATTERN.fullmatch(normalized):
        raise ValueError("TxID TRON должен содержать 64 шестнадцатеричных символа")
    return normalized


def validate_tron_address(value: str) -> str:
    normalized = value.strip()
    if not TRON_ADDRESS_PATTERN.fullmatch(normalized):
        raise ValueError("Некорректный адрес TRON")
    return normalized
