"""Административное управление лотереями, призами и победителями."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.common import MessageResponse, PaginationResponse
from app.schemas.lottery import (
    LotteryAdminRead,
    LotteryAdminTicketRead,
    LotteryCreate,
    LotteryManualWinnerRequest,
    LotteryPrizeCreate,
    LotteryPrizeRead,
    LotteryPrizeUpdate,
    LotterySummaryRead,
    LotteryUpdate,
    LotteryWinnerAdminRead,
    LotteryWinnerConfirmRequest,
)
from app.services.lottery_service import LotteryService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/lotteries", tags=["Администратор: лотереи"])


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", maxsplit=1)[0].strip() or None
    return request.client.host if request.client else None


@router.get("", response_model=PaginationResponse[LotterySummaryRead])
async def list_lotteries(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[LotterySummaryRead]:
    items, total = await LotteryService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.post("", response_model=LotteryAdminRead, status_code=status.HTTP_201_CREATED)
async def create_lottery(
    data: LotteryCreate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryAdminRead:
    item = await LotteryService.create(
        session,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return await LotteryService.get_admin(session, item.id)


@router.get("/{lottery_id}", response_model=LotteryAdminRead)
async def get_lottery(
    lottery_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> LotteryAdminRead:
    return await LotteryService.get_admin(session, lottery_id)


@router.patch("/{lottery_id}", response_model=LotteryAdminRead)
async def update_lottery(
    lottery_id: UUID,
    data: LotteryUpdate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryAdminRead:
    await LotteryService.update(
        session,
        lottery_id=lottery_id,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return await LotteryService.get_admin(session, lottery_id)


@router.post("/{lottery_id}/publish", response_model=LotteryAdminRead)
async def publish_lottery(
    lottery_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryAdminRead:
    await LotteryService.publish(
        session,
        lottery_id=lottery_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return await LotteryService.get_admin(session, lottery_id)


@router.post(
    "/{lottery_id}/prizes",
    response_model=LotteryPrizeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_prize(
    lottery_id: UUID,
    data: LotteryPrizeCreate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryPrizeRead:
    item = await LotteryService.create_prize(
        session,
        lottery_id=lottery_id,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return LotteryPrizeRead.from_prize(item)


@router.patch("/{lottery_id}/prizes/{prize_id}", response_model=LotteryPrizeRead)
async def update_prize(
    lottery_id: UUID,
    prize_id: UUID,
    data: LotteryPrizeUpdate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryPrizeRead:
    item = await LotteryService.update_prize(
        session,
        lottery_id=lottery_id,
        prize_id=prize_id,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return LotteryPrizeRead.from_prize(item)


@router.delete(
    "/{lottery_id}/prizes/{prize_id}", response_model=MessageResponse
)
async def delete_prize(
    lottery_id: UUID,
    prize_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> MessageResponse:
    await LotteryService.delete_prize(
        session,
        lottery_id=lottery_id,
        prize_id=prize_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return MessageResponse(message="Приз удалён")


@router.get(
    "/{lottery_id}/tickets",
    response_model=PaginationResponse[LotteryAdminTicketRead],
)
async def list_tickets(
    lottery_id: UUID,
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
    search: Annotated[str | None, Query(max_length=320)] = None,
) -> PaginationResponse[LotteryAdminTicketRead]:
    items, total = await LotteryService.list_admin_tickets(
        session,
        lottery_id=lottery_id,
        offset=pagination.offset,
        limit=pagination.page_size,
        search=search,
    )
    return PaginationResponse(
        items=items,
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.post("/{lottery_id}/draw-random", response_model=list[LotteryWinnerAdminRead])
async def draw_random(
    lottery_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> list[LotteryWinnerAdminRead]:
    return await LotteryService.draw_random(
        session,
        lottery_id=lottery_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )


@router.post(
    "/{lottery_id}/winners/manual", response_model=LotteryWinnerAdminRead
)
async def select_manual_winner(
    lottery_id: UUID,
    data: LotteryManualWinnerRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryWinnerAdminRead:
    return await LotteryService.select_manual_winner(
        session,
        lottery_id=lottery_id,
        prize_id=data.prize_id,
        ticket_id=data.ticket_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )


@router.delete("/winners/{winner_id}", response_model=MessageResponse)
async def remove_pending_winner(
    winner_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> MessageResponse:
    await LotteryService.remove_pending_winner(
        session,
        winner_id=winner_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return MessageResponse(message="Выбор победителя отменён")


@router.post("/winners/{winner_id}/confirm", response_model=LotteryWinnerAdminRead)
async def confirm_winner(
    winner_id: UUID,
    data: LotteryWinnerConfirmRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> LotteryWinnerAdminRead:
    return await LotteryService.confirm_winner(
        session,
        winner_id=winner_id,
        note=data.note,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )


@router.post(
    "/{lottery_id}/winners/confirm-all",
    response_model=list[LotteryWinnerAdminRead],
)
async def confirm_all_winners(
    lottery_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> list[LotteryWinnerAdminRead]:
    return await LotteryService.confirm_all_winners(
        session,
        lottery_id=lottery_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
