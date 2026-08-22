"""Ответы по активированным программам и календарю начислений."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.db.enums import (
    PlanTier,
    RewardFrequency,
    RewardPayoutStatus,
    UserSubscriptionStatus,
)
from app.schemas.common import APIModel
from app.utils.money import format_amount


class RewardPayoutRead(APIModel):
    id: UUID
    amount: str
    asset: str = "USDT"
    due_at: datetime
    paid_at: datetime | None
    status: RewardPayoutStatus
    attempt_count: int

    @classmethod
    def from_payout(cls, payout: object) -> "RewardPayoutRead":
        return cls(
            id=getattr(payout, "id"),
            amount=format_amount(getattr(payout, "amount_atomic")),
            due_at=getattr(payout, "due_at"),
            paid_at=getattr(payout, "paid_at"),
            status=getattr(payout, "status"),
            attempt_count=getattr(payout, "attempt_count"),
        )


class UserSubscriptionRead(APIModel):
    id: UUID
    plan_id: UUID
    plan_title: str
    plan_tier: PlanTier
    status: UserSubscriptionStatus
    purchased_at: datetime
    access_started_at: datetime
    access_ends_at: datetime
    price: str
    reward_amount: str
    reward_frequency: RewardFrequency
    reward_duration_value: int
    reward_duration_unit: str
    reward_payouts: list[RewardPayoutRead] = Field(default_factory=list)

    @classmethod
    def from_subscription(
        cls, subscription: object, payouts: list[object] | None = None
    ) -> "UserSubscriptionRead":
        plan = getattr(subscription, "plan")
        return cls(
            id=getattr(subscription, "id"),
            plan_id=getattr(subscription, "plan_id"),
            plan_title=plan.title,
            plan_tier=getattr(subscription, "plan_tier"),
            status=getattr(subscription, "status"),
            purchased_at=getattr(subscription, "purchased_at"),
            access_started_at=getattr(subscription, "access_started_at"),
            access_ends_at=getattr(subscription, "access_ends_at"),
            price=format_amount(getattr(subscription, "price_atomic")),
            reward_amount=format_amount(getattr(subscription, "reward_amount_atomic")),
            reward_frequency=getattr(subscription, "reward_frequency"),
            reward_duration_value=getattr(subscription, "reward_duration_value"),
            reward_duration_unit=getattr(subscription, "reward_duration_unit").value,
            reward_payouts=[RewardPayoutRead.from_payout(p) for p in (payouts or [])],
        )
