"""Заявки на ручной вывод USDT ERC-20."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import WithdrawalStatus


class WithdrawalRequest(TimestampMixin, Base):
    __tablename__ = "withdrawal_requests"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    asset: Mapped[str] = mapped_column(String(16), default="USDT", nullable=False)
    network: Mapped[str] = mapped_column(String(32), default="ETHEREUM", nullable=False)
    destination_address: Mapped[str] = mapped_column(String(256), nullable=False)
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fee_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    total_debit_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[WithdrawalStatus] = mapped_column(
        Enum(
            WithdrawalStatus,
            name="withdrawal_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=WithdrawalStatus.PENDING_REVIEW,
        index=True,
        nullable=False,
    )
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    txid: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    approved_by_admin_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    approved_by_admin = relationship("User", foreign_keys=[approved_by_admin_id], lazy="joined")
