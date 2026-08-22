"""Реферальная программа текущего пользователя."""

from fastapi import APIRouter

from app.api.dependencies import CurrentUserDep, SessionDep
from app.schemas.referral import ReferralSummaryRead
from app.services.referral_service import ReferralService

router = APIRouter(prefix="/referrals", tags=["Реферальная программа"])


@router.get("/me", response_model=ReferralSummaryRead)
async def get_my_referrals(
    session: SessionDep, current_user: CurrentUserDep
) -> ReferralSummaryRead:
    return await ReferralService.get_summary(session, user=current_user)
