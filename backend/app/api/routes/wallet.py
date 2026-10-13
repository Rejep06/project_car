"""Внутренний кошелёк, пополнения и заявки на ручной вывод."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentUserDep, OptionalIdempotencyKeyDep, SessionDep
from app.core.config import get_settings
from app.schemas.common import PaginationResponse
from app.schemas.deposit import DepositInvoiceCreate, DepositInvoiceRead
from app.schemas.deposit_wallet import DepositWalletPublicRead
from app.schemas.wallet import WalletRead, WalletTransactionRead
from app.schemas.withdrawal import WithdrawalCreate, WithdrawalRead
from app.services.deposit_service import DepositService
from app.services.deposit_wallet_service import DepositWalletService
from app.services.wallet_service import WalletService
from app.services.withdrawal_service import WithdrawalService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/wallet", tags=["Кошелёк"])


@router.get("", response_model=WalletRead)
async def get_wallet(session: SessionDep, current_user: CurrentUserDep) -> WalletRead:
    return WalletRead.from_wallet(
        await WalletService.get_wallet(session, current_user.id)
    )


@router.get("/transactions", response_model=PaginationResponse[WalletTransactionRead])
async def list_wallet_transactions(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[WalletTransactionRead]:
    items, total = await WalletService.list_transactions(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[WalletTransactionRead.from_transaction(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )




@router.get("/deposit-addresses", response_model=list[DepositWalletPublicRead])
async def list_deposit_addresses(
    session: SessionDep, _: CurrentUserDep
) -> list[DepositWalletPublicRead]:
    items = await DepositWalletService.list_active(session, get_settings())
    return [DepositWalletPublicRead.model_validate(item) for item in items]


@router.post(
    "/deposits",
    response_model=DepositInvoiceRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_deposit_invoice(
    data: DepositInvoiceCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    idempotency_key: OptionalIdempotencyKeyDep,
) -> DepositInvoiceRead:
    settings = get_settings()
    invoice = await DepositService.create_invoice(
        session,
        user=current_user,
        amount=data.amount,
        deposit_wallet_id=data.deposit_wallet_id,
        idempotency_key=idempotency_key,
        settings=settings,
    )
    return DepositInvoiceRead.from_invoice(invoice, settings.network_display_name)


@router.get("/deposits", response_model=PaginationResponse[DepositInvoiceRead])
async def list_deposit_invoices(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[DepositInvoiceRead]:
    settings = get_settings()
    items, total = await DepositService.list_user_invoices(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[
            DepositInvoiceRead.from_invoice(item, settings.network_display_name)
            for item in items
        ],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/deposits/{invoice_id}", response_model=DepositInvoiceRead)
async def get_deposit_invoice(
    invoice_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> DepositInvoiceRead:
    settings = get_settings()
    invoice = await DepositService.get_user_invoice(
        session, user_id=current_user.id, invoice_id=invoice_id
    )
    return DepositInvoiceRead.from_invoice(invoice, settings.network_display_name)


@router.post(
    "/withdrawals",
    response_model=WithdrawalRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_withdrawal(
    data: WithdrawalCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
    idempotency_key: OptionalIdempotencyKeyDep,
) -> WithdrawalRead:
    settings = get_settings()
    item = await WithdrawalService.create(
        session,
        user=current_user,
        destination_address=data.destination_address,
        amount=data.amount,
        idempotency_key=idempotency_key,
        settings=settings,
    )
    return WithdrawalRead.from_withdrawal(item, settings.network_display_name)


@router.get("/withdrawals", response_model=PaginationResponse[WithdrawalRead])
async def list_withdrawals(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[WithdrawalRead]:
    settings = get_settings()
    items, total = await WithdrawalService.list_user(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[
            WithdrawalRead.from_withdrawal(item, settings.network_display_name)
            for item in items
        ],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/withdrawals/{withdrawal_id}", response_model=WithdrawalRead)
async def get_withdrawal(
    withdrawal_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> WithdrawalRead:
    settings = get_settings()
    item = await WithdrawalService.get_user(
        session, user_id=current_user.id, withdrawal_id=withdrawal_id
    )
    return WithdrawalRead.from_withdrawal(item, settings.network_display_name)


@router.post("/withdrawals/{withdrawal_id}/cancel", response_model=WithdrawalRead)
async def cancel_withdrawal(
    withdrawal_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> WithdrawalRead:
    settings = get_settings()
    item = await WithdrawalService.cancel(
        session, user_id=current_user.id, withdrawal_id=withdrawal_id
    )
    return WithdrawalRead.from_withdrawal(item, settings.network_display_name)
