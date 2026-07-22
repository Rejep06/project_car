"""Схемы обращений, сообщений и вложений поддержки."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.db.enums import (
    BinanceDepositStatus,
    SupportTicketCategory,
    SupportTicketStatus,
    UnmatchedDepositStatus,
)
from app.schemas.common import APIModel, validate_txid
from app.utils.money import format_amount


class TicketCreate(APIModel):
    category: SupportTicketCategory
    subject: str = Field(min_length=3, max_length=250)
    message: str = Field(min_length=3, max_length=10000)
    txid: str | None = None
    related_deposit_invoice_id: UUID | None = None

    @field_validator("txid")
    @classmethod
    def validate_optional_txid(cls, value: str | None) -> str | None:
        return validate_txid(value) if value else None

    @model_validator(mode="after")
    def validate_deposit_problem(self) -> "TicketCreate":
        if self.category == SupportTicketCategory.DEPOSIT_PROBLEM and not self.txid:
            raise ValueError("Для проблемы с пополнением необходимо указать TxID")
        return self


class MessageCreate(APIModel):
    message: str = Field(min_length=1, max_length=10000)
    txid: str | None = None

    @field_validator("txid")
    @classmethod
    def validate_optional_txid(cls, value: str | None) -> str | None:
        return validate_txid(value) if value else None


class AttachmentRead(APIModel):
    id: UUID
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
    download_url: str

    @classmethod
    def from_attachment(cls, attachment: object, prefix: str) -> "AttachmentRead":
        return cls(
            id=getattr(attachment, "id"),
            original_filename=getattr(attachment, "original_filename"),
            mime_type=getattr(attachment, "mime_type"),
            size_bytes=getattr(attachment, "size_bytes"),
            created_at=getattr(attachment, "created_at"),
            download_url=f"{prefix}/support/attachments/{getattr(attachment, 'id')}",
        )


class MessageRead(APIModel):
    id: UUID
    author_user_id: UUID
    author_email: str
    message: str
    txid: str | None
    created_at: datetime
    attachments: list[AttachmentRead]

    @classmethod
    def from_message(cls, message: object, prefix: str) -> "MessageRead":
        return cls(
            id=getattr(message, "id"),
            author_user_id=getattr(message, "author_user_id"),
            author_email=getattr(message, "author").email,
            message=getattr(message, "message"),
            txid=getattr(message, "txid"),
            created_at=getattr(message, "created_at"),
            attachments=[
                AttachmentRead.from_attachment(item, prefix)
                for item in getattr(message, "attachments")
            ],
        )


class TicketRead(APIModel):
    id: UUID
    user_id: UUID
    user_email: str
    category: SupportTicketCategory
    subject: str
    status: SupportTicketStatus
    related_deposit_invoice_id: UUID | None
    txid_conflict: bool
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    messages: list[MessageRead]

    @classmethod
    def from_ticket(cls, ticket: object, prefix: str) -> "TicketRead":
        return cls(
            id=getattr(ticket, "id"),
            user_id=getattr(ticket, "user_id"),
            user_email=getattr(ticket, "user").email,
            category=getattr(ticket, "category"),
            subject=getattr(ticket, "subject"),
            status=getattr(ticket, "status"),
            related_deposit_invoice_id=getattr(ticket, "related_deposit_invoice_id"),
            txid_conflict=getattr(ticket, "txid_conflict"),
            created_at=getattr(ticket, "created_at"),
            updated_at=getattr(ticket, "updated_at"),
            closed_at=getattr(ticket, "closed_at"),
            messages=[MessageRead.from_message(item, prefix) for item in getattr(ticket, "messages")],
        )


class AdminTicketRead(TicketRead):
    expected_amount: str | None = None
    actual_amount: str | None = None
    binance_deposit_id: str | None = None
    binance_txid: str | None = None
    binance_address: str | None = None
    binance_network: str | None = None
    binance_status: BinanceDepositStatus | None = None
    binance_detected_at: datetime | None = None
    binance_raw_data: dict[str, Any] | None = None
    txid_already_used: bool = False
    warning: str | None = None

    @classmethod
    def from_ticket(cls, ticket: object, prefix: str) -> "AdminTicketRead":
        base = TicketRead.from_ticket(ticket, prefix).model_dump()
        invoice = getattr(ticket, "related_deposit_invoice", None)
        direct_deposit = getattr(ticket, "related_binance_deposit", None)
        unmatched = getattr(ticket, "related_unmatched_deposit", None)
        deposit = direct_deposit
        if deposit is None and unmatched is not None:
            deposit = unmatched.binance_deposit

        actual_atomic = None
        if deposit is not None:
            actual_atomic = deposit.amount_atomic
        elif unmatched is not None:
            actual_atomic = unmatched.amount_atomic

        conflict = bool(getattr(ticket, "txid_conflict"))
        txid_already_used = bool(
            (deposit is not None and deposit.credited_at is not None)
            or (
                unmatched is not None
                and unmatched.status == UnmatchedDepositStatus.ASSIGNED
            )
        )
        return cls(
            **base,
            expected_amount=(
                format_amount(invoice.expected_amount_atomic) if invoice else None
            ),
            actual_amount=(
                format_amount(actual_atomic) if actual_atomic is not None else None
            ),
            binance_deposit_id=(
                deposit.binance_deposit_id if deposit is not None else None
            ),
            binance_txid=deposit.txid if deposit is not None else None,
            binance_address=deposit.address if deposit is not None else None,
            binance_network=deposit.network if deposit is not None else None,
            binance_status=deposit.status if deposit is not None else None,
            binance_detected_at=deposit.detected_at if deposit is not None else None,
            binance_raw_data=deposit.raw_data if deposit is not None else None,
            txid_already_used=txid_already_used,
            warning=(
                "TxID уже связан с зачислением другому пользователю; "
                "автоматическое изменение баланса запрещено"
                if conflict
                else None
            ),
        )


class TicketStatusUpdate(APIModel):
    status: SupportTicketStatus
