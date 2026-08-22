"""Расчёт и отображение реферальной программы."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.enums import WalletOperationType
from app.db.models import User, UserSubscription, WalletTransaction
from app.schemas.referral import ReferralMemberRead, ReferralSummaryRead
from app.services.wallet_service import WalletService
from app.utils.money import format_amount


def mask_email(email: str) -> str:
    local, separator, domain = email.partition("@")
    if not separator:
        return email
    if len(local) <= 2:
        visible = local[:1]
    else:
        visible = local[:2]
    return f"{visible}***@{domain}"


class ReferralService:
    @staticmethod
    async def get_summary(
        session: AsyncSession,
        *,
        user: User,
        settings: Settings | None = None,
    ) -> ReferralSummaryRead:
        settings = settings or get_settings()
        invited = list(
            (
                await session.scalars(
                    select(User)
                    .where(User.referred_by_user_id == user.id)
                    .order_by(User.created_at.desc())
                )
            ).all()
        )
        invited_ids = [item.id for item in invited]
        active_ids: set[UUID] = set()
        if invited_ids:
            active_ids = set(
                (
                    await session.scalars(
                        select(UserSubscription.user_id)
                        .where(UserSubscription.user_id.in_(invited_ids))
                        .distinct()
                    )
                ).all()
            )

        wallet = await WalletService.get_wallet(session, user.id)
        transactions = list(
            (
                await session.scalars(
                    select(WalletTransaction).where(
                        WalletTransaction.wallet_id == wallet.id,
                        WalletTransaction.operation_type.in_(
                            [
                                WalletOperationType.REFERRAL_PURCHASE_BONUS,
                                WalletOperationType.REFERRAL_REWARD_BONUS,
                            ]
                        ),
                    )
                )
            ).all()
        )
        purchase_total = sum(
            item.available_delta_atomic
            for item in transactions
            if item.operation_type == WalletOperationType.REFERRAL_PURCHASE_BONUS
        )
        reward_total = sum(
            item.available_delta_atomic
            for item in transactions
            if item.operation_type == WalletOperationType.REFERRAL_REWARD_BONUS
        )
        return ReferralSummaryRead(
            referral_code=user.referral_code,
            invited_count=len(invited),
            active_invited_count=len(active_ids),
            total_earned=format_amount(purchase_total + reward_total),
            purchase_bonus_earned=format_amount(purchase_total),
            reward_bonus_earned=format_amount(reward_total),
            purchase_bonus_percent=settings.referral_purchase_bonus_percent,
            premium_reward_bonus=settings.premium_referral_reward_bonus,
            members=[
                ReferralMemberRead(
                    email=mask_email(item.email),
                    joined_at=item.created_at,
                    has_program=item.id in active_ids,
                )
                for item in invited
            ],
        )
