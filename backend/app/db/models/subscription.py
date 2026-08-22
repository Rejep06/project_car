"""Клиентские программы и активированные пользователями программы."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import (
    DurationUnit,
    PlanTier,
    RewardFrequency,
    UserSubscriptionStatus,
)


def enum_column(enum_cls: type, name: str) -> Enum:
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        values_callable=lambda e: [x.value for x in e],
    )


class SubscriptionPlan(TimestampMixin, Base):
    __tablename__ = "subscription_plans"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    tier: Mapped[PlanTier] = mapped_column(
        enum_column(PlanTier, "plan_tier"), index=True, nullable=False
    )
    short_description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    full_description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    access_duration_value: Mapped[int] = mapped_column(Integer, nullable=False)
    access_duration_unit: Mapped[DurationUnit] = mapped_column(
        enum_column(DurationUnit, "access_duration_unit"), nullable=False
    )
    reward_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reward_frequency: Mapped[RewardFrequency] = mapped_column(
        enum_column(RewardFrequency, "reward_frequency"), nullable=False
    )
    reward_duration_value: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_duration_unit: Mapped[DurationUnit] = mapped_column(
        enum_column(DurationUnit, "reward_duration_unit"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    user_subscriptions = relationship("UserSubscription", back_populates="plan", lazy="raise")


class UserSubscription(TimestampMixin, Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    plan_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    plan_tier: Mapped[PlanTier] = mapped_column(
        enum_column(PlanTier, "purchased_plan_tier"), nullable=False
    )
    status: Mapped[UserSubscriptionStatus] = mapped_column(
        enum_column(UserSubscriptionStatus, "user_subscription_status"),
        default=UserSubscriptionStatus.ACTIVE,
        nullable=False,
    )
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    access_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    access_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    price_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reward_amount_atomic: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reward_frequency: Mapped[RewardFrequency] = mapped_column(
        enum_column(RewardFrequency, "purchased_reward_frequency"), nullable=False
    )
    reward_duration_value: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_duration_unit: Mapped[DurationUnit] = mapped_column(
        enum_column(DurationUnit, "purchased_reward_duration_unit"), nullable=False
    )

    plan = relationship("SubscriptionPlan", back_populates="user_subscriptions", lazy="joined")
    user = relationship("User", lazy="joined")
    reward_payouts = relationship("RewardPayout", back_populates="user_subscription", lazy="raise")
