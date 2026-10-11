"""Схемы пользовательских и административных операций вывода."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.enums import WithdrawalStatus
from app.schemas.common import APIModel, validate_evm_address, validate_txid
from app.utils.money import format_amount, parse_amount


class WithdrawalCreate(APIModel):
    destination_address: str
    amount: str

    @field_validator("destination_address")
    @classmethod
    def validate_address(cls, value: str) -> str:
        return validate_evm_address(value)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return format_amount(atomic)


class WithdrawalRead(APIModel):
    id: UUID
    asset: str
    network: str
    destination_address: str
    amount: str
    fee: str
    held_total: str
    final_total: str
    status: WithdrawalStatus
    admin_comment: str | None
    txid: str | None
    approved_at: datetime | None
    sent_at: datetime | None
    completed_at: datetime | None
    rejected_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_withdrawal(cls, item: object, network_display_name: str) -> "WithdrawalRead":
        amount = getattr(item, "amount_atomic")
        fee = getattr(item, "fee_atomic")
        return cls(
            id=getattr(item, "id"),
            asset=getattr(item, "asset"),
            network=network_display_name,
            destination_address=getattr(item, "destination_address"),
            amount=format_amount(amount),
            fee=format_amount(fee),
            held_total=format_amount(getattr(item, "total_debit_atomic")),
            final_total=format_amount(amount + fee),
            status=getattr(item, "status"),
            admin_comment=getattr(item, "admin_comment"),
            txid=getattr(item, "txid"),
            approved_at=getattr(item, "approved_at"),
            sent_at=getattr(item, "sent_at"),
            completed_at=getattr(item, "completed_at"),
            rejected_at=getattr(item, "rejected_at"),
            created_at=getattr(item, "created_at"),
            updated_at=getattr(item, "updated_at"),
        )


class WithdrawalRejectRequest(APIModel):
    comment: str = Field(min_length=3, max_length=1000)


class WithdrawalMarkSentRequest(APIModel):
    txid: str
    actual_fee: str
    comment: str | None = Field(default=None, max_length=1000)

    @field_validator("txid")
    @classmethod
    def validate_txid_field(cls, value: str) -> str:
        return validate_txid(value)

    @field_validator("actual_fee")
    @classmethod
    def validate_fee(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic < 0:
            raise ValueError("Комиссия не может быть отрицательной")
        return format_amount(atomic)


class WithdrawalCompleteRequest(APIModel):
    comment: str | None = Field(default=None, max_length=1000)


class WithdrawalAmountsUpdateRequest(APIModel):
    amount: str
    fee: str
    comment: str = Field(min_length=3, max_length=1000)
    expected_updated_at: datetime

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return format_amount(atomic)

    @field_validator("fee")
    @classmethod
    def validate_fee(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic < 0:
            raise ValueError("Комиссия не может быть отрицательной")
        return format_amount(atomic)

    @field_validator("comment", mode="before")
    @classmethod
    def trim_comment(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AdminWithdrawalRead(WithdrawalRead):
    user_id: UUID
    user_email: str

    @classmethod
    def from_withdrawal(cls, item: object, network_display_name: str) -> "AdminWithdrawalRead":
        base = WithdrawalRead.from_withdrawal(item, network_display_name).model_dump()
        return cls(
            **base,
            user_id=getattr(item, "user_id"),
            user_email=getattr(item, "user").email,
        )
