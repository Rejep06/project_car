"""Покупка и просмотр пользовательских подписок."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentUserDep,
    IdempotencyKeyDep,
    SessionDep,
)
from app.schemas.common import PaginationResponse
from app.schemas.subscription import UserSubscriptionRead
from app.services.subscription_service import SubscriptionService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/subscriptions", tags=["Подписки"])


@router.post(
    "/{plan_id}/purchase",
    response_model=UserSubscriptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def purchase_subscription(
    plan_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    idempotency_key: IdempotencyKeyDep,
) -> UserSubscriptionRead:
    subscription, payouts, _ = await SubscriptionService.purchase(
        session,
        user=current_user,
        plan_id=plan_id,
        idempotency_key=idempotency_key,
    )
    return UserSubscriptionRead.from_subscription(subscription, payouts)


@router.get("", response_model=PaginationResponse[UserSubscriptionRead])
async def list_subscriptions(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[UserSubscriptionRead]:
    items, total = await SubscriptionService.list_user(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[UserSubscriptionRead.from_subscription(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{subscription_id}", response_model=UserSubscriptionRead)
async def get_subscription(
    subscription_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> UserSubscriptionRead:
    item, payouts = await SubscriptionService.get_user_subscription(
        session, user_id=current_user.id, subscription_id=subscription_id
    )
    return UserSubscriptionRead.from_subscription(item, payouts)
