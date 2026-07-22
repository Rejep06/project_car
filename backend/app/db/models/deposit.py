"""Заявки на пополнение, нормализованные Binance-депозиты и ручной разбор."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    BinanceDepositStatus,
    DepositInvoiceStatus,
    UnmatchedDepositReason,
    UnmatchedDepositStatus,
)


def enum_column(enum_cls: type, name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        values_callable=lambda e: [x.value for x in e],
    )


class DepositInvoice(TimestampMixin, Base):
    __tablename__ = "deposit_invoices"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    requested_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_amount_atomic: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    received_amount_atomic: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    asset: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    network: Mapped[str] = mapped_column(String(32), default="TRON", nullable=False)
    deposit_address: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[DepositInvoiceStatus] = mapped_column(
        enum_column(DepositInvoiceStatus, "deposit_invoice_status"),
        default=DepositInvoiceStatus.WAITING,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    amount_reserved_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    matched_binance_deposit_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    credited_after_expiration: Mapped[bool] = mapped_column(default=False, nullable=False)

    user = relationship("User", lazy="joined")
    reservation = relationship(
        "DepositAmountReservation", back_populates="invoice", uselist=False, lazy="joined"
    )
    binance_deposit = relationship("BinanceDeposit", back_populates="deposit_invoice", uselist=False, lazy="raise")


class DepositAmountReservation(Base):
    """Отдельная блокировка точной суммы, гарантирующая уникальность при гонках."""

    __tablename__ = "deposit_amount_reservations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("deposit_invoices.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    expected_amount_atomic: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    reserved_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    invoice = relationship("DepositInvoice", back_populates="reservation", lazy="joined")


class BinanceDeposit(TimestampMixin, Base):
    __tablename__ = "binance_deposits"
    __table_args__ = (UniqueConstraint("network", "txid", name="uq_binance_deposit_network_txid"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    binance_deposit_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    txid: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    coin: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str] = mapped_column(String(32), nullable=False)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[BinanceDepositStatus] = mapped_column(
        enum_column(BinanceDepositStatus, "binance_deposit_status"), nullable=False
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    deposit_invoice_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("deposit_invoices.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deposit_invoice = relationship("DepositInvoice", back_populates="binance_deposit", lazy="joined")
    unmatched = relationship("UnmatchedDeposit", back_populates="binance_deposit", uselist=False, lazy="raise")


class UnmatchedDeposit(Base):
    __tablename__ = "unmatched_deposits"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    binance_deposit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("binance_deposits.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    txid: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    network: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[UnmatchedDepositReason] = mapped_column(
        enum_column(UnmatchedDepositReason, "unmatched_deposit_reason"), nullable=False
    )
    status: Mapped[UnmatchedDepositStatus] = mapped_column(
        enum_column(UnmatchedDepositStatus, "unmatched_deposit_status"),
        default=UnmatchedDepositStatus.UNRESOLVED,
        index=True,
        nullable=False,
    )
    assigned_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_invoice_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("deposit_invoices.id", ondelete="SET NULL"), nullable=True
    )
    assigned_by_admin_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    binance_deposit = relationship("BinanceDeposit", back_populates="unmatched", lazy="joined")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined")
    assigned_invoice = relationship("DepositInvoice", lazy="joined")
