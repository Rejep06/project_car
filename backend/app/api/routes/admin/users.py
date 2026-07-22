"""Просмотр пользователей, заморозка и журналируемая корректировка."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import (
    CurrentAdminDep,
    IdempotencyKeyDep,
    SessionDep,
)
from app.schemas.common import PaginationResponse
from app.schemas.user import AdminUserRead
from app.schemas.wallet import BalanceAdjustmentRequest
from app.services.user_service import UserService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/users", tags=["Администратор: пользователи"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginationResponse[AdminUserRead])
async def list_users(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[AdminUserRead]:
    items, total = await UserService.list_users(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[AdminUserRead.from_user(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{user_id}", response_model=AdminUserRead)
async def get_user(
    user_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> AdminUserRead:
    return AdminUserRead.from_user(await UserService.get_user(session, user_id))


@router.post("/{user_id}/freeze", response_model=AdminUserRead)
async def freeze_user(
    user_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminUserRead:
    await UserService.set_frozen(
        session,
        user_id=user_id,
        is_frozen=True,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return AdminUserRead.from_user(await UserService.get_user(session, user_id))


@router.post("/{user_id}/unfreeze", response_model=AdminUserRead)
async def unfreeze_user(
    user_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminUserRead:
    await UserService.set_frozen(
        session,
        user_id=user_id,
        is_frozen=False,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return AdminUserRead.from_user(await UserService.get_user(session, user_id))


@router.post("/{user_id}/balance-adjustment", response_model=AdminUserRead)
async def adjust_balance(
    user_id: UUID,
    data: BalanceAdjustmentRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
    idempotency_key: IdempotencyKeyDep,
) -> AdminUserRead:
    user = await UserService.adjust_balance(
        session,
        user_id=user_id,
        amount=data.amount,
        description=data.description,
        idempotency_key=idempotency_key,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return AdminUserRead.from_user(user)
