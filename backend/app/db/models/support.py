"""Обращения поддержки, сообщения и защищённые вложения."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import SupportTicketCategory, SupportTicketStatus


class SupportTicket(TimestampMixin, Base):
    __tablename__ = "support_tickets"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    category: Mapped[SupportTicketCategory] = mapped_column(
        Enum(
            SupportTicketCategory,
            name="support_ticket_category",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[SupportTicketStatus] = mapped_column(
        Enum(
            SupportTicketStatus,
            name="support_ticket_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=SupportTicketStatus.OPEN,
        index=True,
        nullable=False,
    )
    related_deposit_invoice_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("deposit_invoices.id", ondelete="SET NULL"), nullable=True
    )
    related_binance_deposit_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("binance_deposits.id", ondelete="SET NULL"), nullable=True
    )
    related_unmatched_deposit_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("unmatched_deposits.id", ondelete="SET NULL"), nullable=True
    )
    txid_conflict: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", lazy="joined")
    related_deposit_invoice = relationship("DepositInvoice", lazy="joined")
    related_binance_deposit = relationship("BinanceDeposit", lazy="joined")
    related_unmatched_deposit = relationship("UnmatchedDeposit", lazy="joined")
    messages = relationship(
        "SupportMessage",
        back_populates="ticket",
        order_by="SupportMessage.created_at",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    txid: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    ticket = relationship("SupportTicket", back_populates="messages", lazy="joined")
    author = relationship("User", lazy="joined")
    attachments = relationship(
        "SupportAttachment",
        back_populates="message",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class SupportAttachment(Base):
    __tablename__ = "support_attachments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("support_messages.id", ondelete="CASCADE"), index=True, nullable=False
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    message = relationship("SupportMessage", back_populates="attachments", lazy="joined")
