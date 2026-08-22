"""Внутренний кошелёк и неизменяемый журнал операций."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum, ForeignKey, JSON, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import WalletOperationType
from app.utils.datetime import utcnow


class Wallet(TimestampMixin, Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("available_balance_atomic >= 0", name="available_nonnegative"),
        CheckConstraint("locked_balance_atomic >= 0", name="locked_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    asset: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    available_balance_atomic: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    locked_balance_atomic: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    user = relationship("User", back_populates="wallet", lazy="selectin")
    transactions = relationship("WalletTransaction", back_populates="wallet", lazy="raise")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        CheckConstraint("available_after_atomic >= 0", name="available_after_nonnegative"),
        CheckConstraint("locked_after_atomic >= 0", name="locked_after_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    wallet_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("wallets.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    operation_type: Mapped[WalletOperationType] = mapped_column(
        Enum(
            WalletOperationType,
            name="wallet_operation_type",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
    )
    available_delta_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    locked_delta_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    available_after_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    locked_after_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    related_entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    related_entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow, server_default=func.now(), index=True, nullable=False
    )

    wallet = relationship("Wallet", back_populates="transactions", lazy="selectin")


@event.listens_for(WalletTransaction, "before_update")
def prevent_wallet_transaction_update(*_: object) -> None:
    raise RuntimeError("WalletTransaction является неизменяемой записью")


@event.listens_for(WalletTransaction, "before_delete")
def prevent_wallet_transaction_delete(*_: object) -> None:
    raise RuntimeError("WalletTransaction нельзя удалять")
