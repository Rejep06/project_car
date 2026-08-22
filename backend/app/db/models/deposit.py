"""Заявки на пополнение, события блокчейна и ручной разбор переводов."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    BlockchainDepositStatus,
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
    deposit_wallet_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("deposit_wallets.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    requested_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_amount_atomic: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    received_amount_atomic: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    asset: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    network: Mapped[str] = mapped_column(String(64), default="ETHEREUM", nullable=False)
    deposit_address: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[DepositInvoiceStatus] = mapped_column(
        enum_column(DepositInvoiceStatus, "deposit_invoice_status"),
        default=DepositInvoiceStatus.WAITING,
        index=True,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    amount_reserved_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    matched_blockchain_deposit_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), nullable=True
    )
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    credited_after_expiration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user = relationship("User", lazy="joined")
    deposit_wallet = relationship("DepositWallet", back_populates="deposit_invoices", lazy="joined")
    reservation = relationship(
        "DepositAmountReservation", back_populates="invoice", uselist=False, lazy="joined"
    )
    blockchain_deposit = relationship(
        "BlockchainDeposit", back_populates="deposit_invoice", uselist=False, lazy="raise"
    )


class DepositAmountReservation(Base):
    """Блокировка точной суммы, гарантирующая уникальность при гонках."""

    __tablename__ = "deposit_amount_reservations"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    invoice_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("deposit_invoices.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    expected_amount_atomic: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    reserved_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )

    invoice = relationship("DepositInvoice", back_populates="reservation", lazy="joined")


class BlockchainDeposit(TimestampMixin, Base):
    """Нормализованное подтверждённое событие входящего перевода."""

    __tablename__ = "blockchain_deposits"
    __table_args__ = (
        UniqueConstraint(
            "network", "txid", "log_index", name="uq_blockchain_deposit_network_txid_log"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    external_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    txid: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    log_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    block_number: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    block_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    asset: Mapped[str] = mapped_column(String(32), nullable=False)
    network: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), default="infura", nullable=False)
    token_contract_address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[BlockchainDepositStatus] = mapped_column(
        enum_column(BlockchainDepositStatus, "blockchain_deposit_status"), nullable=False
    )
    confirmations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    deposit_invoice_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("deposit_invoices.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
    )
    credited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deposit_invoice = relationship(
        "DepositInvoice", back_populates="blockchain_deposit", lazy="joined"
    )
    unmatched = relationship(
        "UnmatchedDeposit", back_populates="blockchain_deposit", uselist=False, lazy="raise"
    )


class BlockchainSyncState(TimestampMixin, Base):
    """Курсор сканирования блоков для конкретной конфигурации провайдера."""

    __tablename__ = "blockchain_sync_states"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    sync_key: Mapped[str] = mapped_column(String(500), unique=True, index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_network: Mapped[str] = mapped_column(String(80), nullable=False)
    chain_id: Mapped[int] = mapped_column(Integer, nullable=False)
    network: Mapped[str] = mapped_column(String(64), nullable=False)
    token_contract_address: Mapped[str] = mapped_column(String(256), nullable=False)
    last_scanned_block: Mapped[int] = mapped_column(BigInteger, nullable=False)


class UnmatchedDeposit(Base):
    __tablename__ = "unmatched_deposits"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    blockchain_deposit_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("blockchain_deposits.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    txid: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    address: Mapped[str] = mapped_column(String(256), nullable=False)
    network: Mapped[str] = mapped_column(String(64), nullable=False)
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

    blockchain_deposit = relationship(
        "BlockchainDeposit", back_populates="unmatched", lazy="joined"
    )
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], lazy="joined")
    assigned_invoice = relationship("DepositInvoice", lazy="joined")
