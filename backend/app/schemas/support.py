"""Схемы обращений поддержки."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.db.enums import (
    BlockchainDepositStatus,
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
            raise ValueError("Для проблемы с пополнением необходимо указать хеш транзакции")
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
    read_at: datetime | None
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
            read_at=getattr(message, "read_at"),
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
    unread_count: int
    messages: list[MessageRead]

    @classmethod
    def from_ticket(
        cls, ticket: object, prefix: str, *, for_admin: bool = False
    ) -> "TicketRead":
        messages = getattr(ticket, "messages")
        owner_id = getattr(ticket, "user_id")
        unread_count = sum(
            item.read_at is None
            and ((item.author_user_id == owner_id) if for_admin else (item.author_user_id != owner_id))
            for item in messages
        )
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
            unread_count=unread_count,
            messages=[MessageRead.from_message(item, prefix) for item in messages],
        )


class AdminTicketRead(TicketRead):
    expected_amount: str | None = None
    actual_amount: str | None = None
    deposit_event_id: str | None = None
    deposit_txid: str | None = None
    deposit_address: str | None = None
    deposit_network: str | None = None
    deposit_status: BlockchainDepositStatus | None = None
    deposit_detected_at: datetime | None = None
    deposit_raw_data: dict[str, Any] | None = None
    txid_already_used: bool = False
    warning: str | None = None

    @classmethod
    def from_ticket(cls, ticket: object, prefix: str) -> "AdminTicketRead":
        base = TicketRead.from_ticket(ticket, prefix, for_admin=True).model_dump()
        invoice = getattr(ticket, "related_deposit_invoice", None)
        direct_deposit = getattr(ticket, "related_blockchain_deposit", None)
        unmatched = getattr(ticket, "related_unmatched_deposit", None)
        deposit = direct_deposit
        if deposit is None and unmatched is not None:
            deposit = unmatched.blockchain_deposit

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
            expected_amount=(format_amount(invoice.expected_amount_atomic) if invoice else None),
            actual_amount=(format_amount(actual_atomic) if actual_atomic is not None else None),
            deposit_event_id=(deposit.external_id if deposit is not None else None),
            deposit_txid=deposit.txid if deposit is not None else None,
            deposit_address=deposit.address if deposit is not None else None,
            deposit_network=deposit.network if deposit is not None else None,
            deposit_status=deposit.status if deposit is not None else None,
            deposit_detected_at=deposit.detected_at if deposit is not None else None,
            deposit_raw_data=deposit.raw_data if deposit is not None else None,
            txid_already_used=txid_already_used,
            warning=(
                "Хеш транзакции уже связан с зачислением другому пользователю; "
                "автоматическое изменение баланса запрещено"
                if conflict
                else None
            ),
        )


class TicketStatusUpdate(APIModel):
    status: SupportTicketStatus


class SupportUnreadCount(APIModel):
    unread_count: int


class TicketMessagesRead(APIModel):
    """Acknowledge only the incoming messages actually shown to the viewer."""

    message_ids: list[UUID] = Field(min_length=1, max_length=1000)
