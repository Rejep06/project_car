"""Схемы клиентских программ."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.enums import DurationUnit, PlanTier, RewardFrequency
from app.schemas.common import APIModel
from app.utils.money import format_amount, parse_amount


class PlanBase(APIModel):
    title: str = Field(min_length=1, max_length=200)
    tier: PlanTier
    short_description: str = Field(default="", max_length=500)
    full_description: str = ""
    image_url: str | None = Field(default=None, max_length=1000)
    price: str
    access_duration_value: int = Field(ge=1, le=1000)
    access_duration_unit: DurationUnit
    reward_amount: str
    reward_frequency: RewardFrequency
    reward_duration_value: int = Field(ge=1, le=1000)
    reward_duration_unit: DurationUnit
    is_active: bool = True

    @field_validator("price", "reward_amount")
    @classmethod
    def validate_money(cls, value: str) -> str:
        atomic = parse_amount(value)
        if atomic < 0:
            raise ValueError("Сумма не может быть отрицательной")
        return format_amount(atomic)


class PlanCreate(PlanBase):
    """Полный набор полей новой программы."""


class PlanUpdate(APIModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    tier: PlanTier | None = None
    short_description: str | None = Field(default=None, max_length=500)
    full_description: str | None = None
    image_url: str | None = Field(default=None, max_length=1000)
    price: str | None = None
    access_duration_value: int | None = Field(default=None, ge=1, le=1000)
    access_duration_unit: DurationUnit | None = None
    reward_amount: str | None = None
    reward_frequency: RewardFrequency | None = None
    reward_duration_value: int | None = Field(default=None, ge=1, le=1000)
    reward_duration_unit: DurationUnit | None = None

    @field_validator("price", "reward_amount")
    @classmethod
    def validate_money(cls, value: str | None) -> str | None:
        if value is None:
            return None
        atomic = parse_amount(value)
        if atomic < 0:
            raise ValueError("Сумма не может быть отрицательной")
        return format_amount(atomic)


class PlanRead(APIModel):
    id: UUID
    title: str
    tier: PlanTier
    short_description: str
    full_description: str
    image_url: str | None
    price: str
    asset: str = "USDT"
    access_duration_value: int
    access_duration_unit: DurationUnit
    reward_amount: str
    reward_frequency: RewardFrequency
    reward_duration_value: int
    reward_duration_unit: DurationUnit
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_plan(cls, plan: object) -> "PlanRead":
        return cls(
            id=getattr(plan, "id"),
            title=getattr(plan, "title"),
            tier=getattr(plan, "tier"),
            short_description=getattr(plan, "short_description"),
            full_description=getattr(plan, "full_description"),
            image_url=getattr(plan, "image_url"),
            price=format_amount(getattr(plan, "price_atomic")),
            access_duration_value=getattr(plan, "access_duration_value"),
            access_duration_unit=getattr(plan, "access_duration_unit"),
            reward_amount=format_amount(getattr(plan, "reward_amount_atomic")),
            reward_frequency=getattr(plan, "reward_frequency"),
            reward_duration_value=getattr(plan, "reward_duration_value"),
            reward_duration_unit=getattr(plan, "reward_duration_unit"),
            is_active=getattr(plan, "is_active"),
            created_at=getattr(plan, "created_at"),
            updated_at=getattr(plan, "updated_at"),
        )
