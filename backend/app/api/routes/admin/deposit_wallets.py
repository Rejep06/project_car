"""Административное управление адресами пополнения."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.deposit_wallet import (
    DepositWalletCreate,
    DepositWalletRead,
    DepositWalletUpdate,
)
from app.services.deposit_wallet_service import DepositWalletService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/deposit-wallets", tags=["Администратор: адреса пополнения"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PaginationResponse[DepositWalletRead])
async def list_wallets(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[DepositWalletRead]:
    items, total = await DepositWalletService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[DepositWalletRead.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.post("", response_model=DepositWalletRead, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    data: DepositWalletCreate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> DepositWalletRead:
    item = await DepositWalletService.create(
        session,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return DepositWalletRead.model_validate(item)


@router.get("/{wallet_id}", response_model=DepositWalletRead)
async def get_wallet(
    wallet_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> DepositWalletRead:
    return DepositWalletRead.model_validate(
        await DepositWalletService.get_admin(session, wallet_id)
    )


@router.patch("/{wallet_id}", response_model=DepositWalletRead)
async def update_wallet(
    wallet_id: UUID,
    data: DepositWalletUpdate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> DepositWalletRead:
    item = await DepositWalletService.update(
        session,
        wallet_id=wallet_id,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return DepositWalletRead.model_validate(item)
