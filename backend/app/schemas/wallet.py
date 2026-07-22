"""Ответы по кошельку и неизменяемому журналу."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.enums import WalletOperationType
from app.schemas.common import APIModel
from app.utils.money import format_amount, parse_amount


class WalletRead(APIModel):
    id: UUID
    asset: str
    available_balance: str
    locked_balance: str
    updated_at: datetime

    @classmethod
    def from_wallet(cls, wallet: object) -> "WalletRead":
        return cls(
            id=getattr(wallet, "id"),
            asset=getattr(wallet, "asset"),
            available_balance=format_amount(getattr(wallet, "available_balance_atomic")),
            locked_balance=format_amount(getattr(wallet, "locked_balance_atomic")),
            updated_at=getattr(wallet, "updated_at"),
        )


class WalletTransactionRead(APIModel):
    id: UUID
    operation_type: WalletOperationType
    available_delta: str
    locked_delta: str
    available_after: str
    locked_after: str
    description: str
    related_entity_type: str | None
    related_entity_id: UUID | None
    created_at: datetime

    @classmethod
    def from_transaction(cls, transaction: object) -> "WalletTransactionRead":
        return cls(
            id=getattr(transaction, "id"),
            operation_type=getattr(transaction, "operation_type"),
            available_delta=format_amount(getattr(transaction, "available_delta_atomic")),
            locked_delta=format_amount(getattr(transaction, "locked_delta_atomic")),
            available_after=format_amount(getattr(transaction, "available_after_atomic")),
            locked_after=format_amount(getattr(transaction, "locked_after_atomic")),
            description=getattr(transaction, "description"),
            related_entity_type=getattr(transaction, "related_entity_type"),
            related_entity_id=getattr(transaction, "related_entity_id"),
            created_at=getattr(transaction, "created_at"),
        )


class BalanceAdjustmentRequest(APIModel):
    amount: str
    description: str = Field(min_length=3, max_length=500)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic == 0:
            raise ValueError("Корректировка не может быть нулевой")
        return format_amount(atomic)
