"""Схемы заявок на пополнение и ручного разбора депозитов."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.enums import (
    BinanceDepositStatus,
    DepositInvoiceStatus,
    UnmatchedDepositReason,
    UnmatchedDepositStatus,
)
from app.schemas.common import APIModel
from app.utils.money import format_amount, parse_amount

DEPOSIT_WARNING = (
    "Отправьте точную сумму через сеть TRON (TRC20). "
    "Проверьте, сколько получит адрес после комиссии биржи. "
    "Перевод через другую сеть может быть потерян."
)


class DepositInvoiceCreate(APIModel):
    amount: str

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return format_amount(atomic)


class DepositInvoiceRead(APIModel):
    id: UUID
    asset: str
    network: str
    address: str
    requested_amount: str
    expected_amount: str
    received_amount: str | None
    expires_at: datetime
    amount_reserved_until: datetime
    status: DepositInvoiceStatus
    credited_at: datetime | None
    credited_after_expiration: bool
    warning: str = DEPOSIT_WARNING
    created_at: datetime

    @classmethod
    def from_invoice(cls, invoice: object, network_display_name: str) -> "DepositInvoiceRead":
        received = getattr(invoice, "received_amount_atomic")
        return cls(
            id=getattr(invoice, "id"),
            asset=getattr(invoice, "asset"),
            network=network_display_name,
            address=getattr(invoice, "deposit_address"),
            requested_amount=format_amount(getattr(invoice, "requested_amount_atomic")),
            expected_amount=format_amount(getattr(invoice, "expected_amount_atomic")),
            received_amount=format_amount(received) if received is not None else None,
            expires_at=getattr(invoice, "expires_at"),
            amount_reserved_until=getattr(invoice, "amount_reserved_until"),
            status=getattr(invoice, "status"),
            credited_at=getattr(invoice, "credited_at"),
            credited_after_expiration=getattr(invoice, "credited_after_expiration", False),
            created_at=getattr(invoice, "created_at"),
        )


class UnmatchedDepositRead(APIModel):
    id: UUID
    binance_record_id: UUID
    binance_deposit_id: str
    txid: str
    coin: str
    amount: str
    address: str
    network: str
    binance_status: BinanceDepositStatus
    deposit_time: datetime
    credited_at: datetime | None
    txid_already_used: bool
    reason: UnmatchedDepositReason
    status: UnmatchedDepositStatus
    assigned_user_id: UUID | None
    assigned_invoice_id: UUID | None
    assigned_at: datetime | None
    created_at: datetime

    @classmethod
    def from_unmatched(cls, item: object) -> "UnmatchedDepositRead":
        deposit = getattr(item, "binance_deposit")
        return cls(
            id=getattr(item, "id"),
            binance_record_id=getattr(item, "binance_deposit_id"),
            binance_deposit_id=getattr(deposit, "binance_deposit_id"),
            txid=getattr(item, "txid"),
            coin=getattr(deposit, "coin"),
            amount=format_amount(getattr(item, "amount_atomic")),
            address=getattr(item, "address"),
            network=getattr(item, "network"),
            binance_status=getattr(deposit, "status"),
            deposit_time=getattr(deposit, "detected_at"),
            credited_at=getattr(deposit, "credited_at"),
            txid_already_used=getattr(deposit, "credited_at") is not None,
            reason=getattr(item, "reason"),
            status=getattr(item, "status"),
            assigned_user_id=getattr(item, "assigned_user_id"),
            assigned_invoice_id=getattr(item, "assigned_invoice_id"),
            assigned_at=getattr(item, "assigned_at"),
            created_at=getattr(item, "created_at"),
        )


class AssignDepositRequest(APIModel):
    user_id: UUID
    invoice_id: UUID | None = None


class ResolveTicketDepositRequest(APIModel):
    invoice_id: UUID | None = None
