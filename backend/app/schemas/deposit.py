"""Схемы заявок на пополнение и ручного разбора переводов."""

from datetime import datetime
from uuid import UUID

from pydantic import field_validator

from app.db.enums import (
    BlockchainDepositStatus,
    DepositInvoiceStatus,
    UnmatchedDepositReason,
    UnmatchedDepositStatus,
)
from app.schemas.common import APIModel
from app.utils.money import format_amount, parse_amount

DEPOSIT_WARNING = (
    "Переведите точную сумму на указанный адрес в выбранной сети. "
    "Сумма, которая поступит после комиссии отправителя, должна совпасть полностью."
)


class DepositInvoiceCreate(APIModel):
    amount: str
    deposit_wallet_id: UUID | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return format_amount(atomic)


class DepositInvoiceRead(APIModel):
    id: UUID
    deposit_wallet_id: UUID | None
    wallet_name: str
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
        wallet = getattr(invoice, "deposit_wallet", None)
        return cls(
            id=getattr(invoice, "id"),
            deposit_wallet_id=getattr(invoice, "deposit_wallet_id", None),
            wallet_name=getattr(wallet, "title", None) or "Кошелёк пополнения",
            asset=getattr(invoice, "asset"),
            network=getattr(wallet, "network_display_name", None) or network_display_name,
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
    blockchain_record_id: UUID
    event_id: str
    txid: str
    log_index: int
    block_number: int | None
    block_hash: str | None
    from_address: str | None
    asset: str
    amount: str
    address: str
    network: str
    provider: str
    token_contract_address: str | None
    deposit_status: BlockchainDepositStatus
    confirmations: int
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
        deposit = getattr(item, "blockchain_deposit")
        return cls(
            id=getattr(item, "id"),
            blockchain_record_id=getattr(item, "blockchain_deposit_id"),
            event_id=getattr(deposit, "external_id"),
            txid=getattr(item, "txid"),
            log_index=getattr(deposit, "log_index"),
            block_number=getattr(deposit, "block_number"),
            block_hash=getattr(deposit, "block_hash"),
            from_address=getattr(deposit, "from_address"),
            asset=getattr(deposit, "asset"),
            amount=format_amount(getattr(item, "amount_atomic")),
            address=getattr(item, "address"),
            network=getattr(item, "network"),
            provider=getattr(deposit, "provider"),
            token_contract_address=getattr(deposit, "token_contract_address"),
            deposit_status=getattr(deposit, "status"),
            confirmations=getattr(deposit, "confirmations"),
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
