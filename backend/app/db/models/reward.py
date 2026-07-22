"""Заранее рассчитанные выплаты вознаграждений."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import RewardPayoutStatus


class RewardPayout(TimestampMixin, Base):
    __tablename__ = "reward_payouts"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_subscription_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("user_subscriptions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[RewardPayoutStatus] = mapped_column(
        Enum(
            RewardPayoutStatus,
            name="reward_payout_status",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=RewardPayoutStatus.PENDING,
        index=True,
        nullable=False,
    )
    wallet_transaction_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("wallet_transactions.id", ondelete="RESTRICT"), nullable=True
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_subscription = relationship("UserSubscription", back_populates="reward_payouts", lazy="joined")
    wallet_transaction = relationship("WalletTransaction", lazy="joined")
