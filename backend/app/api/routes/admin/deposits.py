"""Ручной разбор нераспознанных Binance-депозитов."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.deposit import AssignDepositRequest, UnmatchedDepositRead
from app.services.deposit_service import DepositService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/deposits", tags=["Администратор: депозиты"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/unmatched", response_model=PaginationResponse[UnmatchedDepositRead])
async def list_unmatched(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[UnmatchedDepositRead]:
    items, total = await DepositService.list_unmatched(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[UnmatchedDepositRead.from_unmatched(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/unmatched/{unmatched_id}", response_model=UnmatchedDepositRead)
async def get_unmatched(
    unmatched_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> UnmatchedDepositRead:
    return UnmatchedDepositRead.from_unmatched(
        await DepositService.get_unmatched(session, unmatched_id)
    )


@router.post("/unmatched/{unmatched_id}/assign", response_model=UnmatchedDepositRead)
async def assign_unmatched(
    unmatched_id: UUID,
    data: AssignDepositRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> UnmatchedDepositRead:
    item = await DepositService.assign_unmatched(
        session,
        unmatched_id=unmatched_id,
        user_id=data.user_id,
        invoice_id=data.invoice_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return UnmatchedDepositRead.from_unmatched(item)


@router.post("/unmatched/{unmatched_id}/ignore", response_model=UnmatchedDepositRead)
async def ignore_unmatched(
    unmatched_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> UnmatchedDepositRead:
    item = await DepositService.ignore_unmatched(
        session,
        unmatched_id=unmatched_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return UnmatchedDepositRead.from_unmatched(item)
