"""Административный процесс ручного вывода средств."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentAdminDep, IdempotencyKeyDep, SessionDep
from app.core.config import get_settings
from app.schemas.common import PaginationResponse
from app.schemas.withdrawal import (
    AdminWithdrawalRead,
    WithdrawalAmountsUpdateRequest,
    WithdrawalCompleteRequest,
    WithdrawalMarkSentRequest,
    WithdrawalRejectRequest,
)
from app.services.withdrawal_service import WithdrawalService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/withdrawals", tags=["Администратор: выводы"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def serialize(item: object) -> AdminWithdrawalRead:
    return AdminWithdrawalRead.from_withdrawal(
        item, get_settings().network_display_name
    )


@router.get("", response_model=PaginationResponse[AdminWithdrawalRead])
async def list_withdrawals(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[AdminWithdrawalRead]:
    items, total = await WithdrawalService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[serialize(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{withdrawal_id}", response_model=AdminWithdrawalRead)
async def get_withdrawal(
    withdrawal_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> AdminWithdrawalRead:
    return serialize(await WithdrawalService.get_admin(session, withdrawal_id))


@router.post("/{withdrawal_id}/approve", response_model=AdminWithdrawalRead)
async def approve_withdrawal(
    withdrawal_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminWithdrawalRead:
    return serialize(
        await WithdrawalService.approve(
            session,
            withdrawal_id=withdrawal_id,
            admin_user_id=admin.id,
            ip_address=client_ip(request),
        )
    )


@router.patch("/{withdrawal_id}/amounts", response_model=AdminWithdrawalRead)
async def update_withdrawal_amounts(
    withdrawal_id: UUID,
    data: WithdrawalAmountsUpdateRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
    idempotency_key: IdempotencyKeyDep,
) -> AdminWithdrawalRead:
    return serialize(
        await WithdrawalService.update_amounts(
            session,
            withdrawal_id=withdrawal_id,
            amount=data.amount,
            fee=data.fee,
            comment=data.comment,
            expected_updated_at=data.expected_updated_at,
            idempotency_key=idempotency_key,
            admin_user_id=admin.id,
            ip_address=client_ip(request),
        )
    )


@router.post("/{withdrawal_id}/reject", response_model=AdminWithdrawalRead)
async def reject_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalRejectRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminWithdrawalRead:
    return serialize(
        await WithdrawalService.reject(
            session,
            withdrawal_id=withdrawal_id,
            comment=data.comment,
            admin_user_id=admin.id,
            ip_address=client_ip(request),
        )
    )


@router.post("/{withdrawal_id}/mark-sent", response_model=AdminWithdrawalRead)
async def mark_withdrawal_sent(
    withdrawal_id: UUID,
    data: WithdrawalMarkSentRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminWithdrawalRead:
    return serialize(
        await WithdrawalService.mark_sent(
            session,
            withdrawal_id=withdrawal_id,
            txid=data.txid,
            actual_fee=data.actual_fee,
            comment=data.comment,
            admin_user_id=admin.id,
            ip_address=client_ip(request),
        )
    )


@router.post("/{withdrawal_id}/complete", response_model=AdminWithdrawalRead)
async def complete_withdrawal(
    withdrawal_id: UUID,
    data: WithdrawalCompleteRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminWithdrawalRead:
    return serialize(
        await WithdrawalService.complete(
            session,
            withdrawal_id=withdrawal_id,
            comment=data.comment,
            admin_user_id=admin.id,
            ip_address=client_ip(request),
        )
    )
