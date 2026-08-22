"""Схемы реферальной программы пользователя."""

from datetime import datetime

from app.schemas.common import APIModel


class ReferralMemberRead(APIModel):
    email: str
    joined_at: datetime
    has_program: bool


class ReferralSummaryRead(APIModel):
    referral_code: str
    invited_count: int
    active_invited_count: int
    total_earned: str
    purchase_bonus_earned: str
    reward_bonus_earned: str
    purchase_bonus_percent: int
    premium_reward_bonus: str
    members: list[ReferralMemberRead]
