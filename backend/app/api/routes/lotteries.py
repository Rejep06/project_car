"""Публичный каталог лотерей и билеты текущего пользователя."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import CurrentUserDep, IdempotencyKeyDep, SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.lottery import (
    LotteryDetailRead,
    LotteryPurchaseRead,
    LotterySummaryRead,
    LotteryTicketPurchaseRequest,
    LotteryTicketRead,
)
from app.services.lottery_service import LotteryService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/lotteries", tags=["Лотереи"])


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip() or None
    return request.client.host if request.client else None


@router.get("", response_model=PaginationResponse[LotterySummaryRead])
async def list_lotteries(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[LotterySummaryRead]:
    items, total = await LotteryService.list_public(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/me/tickets", response_model=PaginationResponse[LotteryTicketRead])
async def list_my_tickets(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[LotteryTicketRead]:
    items, total = await LotteryService.list_user_tickets(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{lottery_id}", response_model=LotteryDetailRead)
async def get_lottery(lottery_id: UUID, session: SessionDep) -> LotteryDetailRead:
    return await LotteryService.get_public(session, lottery_id)


@router.get("/{lottery_id}/my-tickets", response_model=list[LotteryTicketRead])
async def get_my_lottery_tickets(
    lottery_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> list[LotteryTicketRead]:
    return await LotteryService.list_user_lottery_tickets(
        session, user_id=current_user.id, lottery_id=lottery_id
    )


@router.post(
    "/{lottery_id}/tickets",
    response_model=LotteryPurchaseRead,
    status_code=status.HTTP_201_CREATED,
)
async def buy_tickets(
    lottery_id: UUID,
    data: LotteryTicketPurchaseRequest,
    request: Request,
    session: SessionDep,
    current_user: CurrentUserDep,
    idempotency_key: IdempotencyKeyDep,
) -> LotteryPurchaseRead:
    return await LotteryService.purchase(
        session,
        user=current_user,
        lottery_id=lottery_id,
        quantity=data.quantity,
        idempotency_key=idempotency_key,
        ip_address=client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
