"""Административная обработка обращений и проблемных депозитов."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.core.config import get_settings
from app.schemas.common import PaginationResponse
from app.schemas.deposit import ResolveTicketDepositRequest
from app.schemas.support import (
    AdminTicketRead,
    MessageCreate,
    MessageRead,
    SupportUnreadCount,
    TicketMessagesRead,
    TicketStatusUpdate,
)
from app.services.support_service import SupportService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/support", tags=["Администратор: поддержка"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/unread-count", response_model=SupportUnreadCount)
async def unread_count(
    session: SessionDep, admin: CurrentAdminDep
) -> SupportUnreadCount:
    return SupportUnreadCount(
        unread_count=await SupportService.unread_count(
            session, user_id=admin.id, is_admin=True
        )
    )


@router.post("/tickets/{ticket_id}/read", response_model=SupportUnreadCount)
async def mark_ticket_messages_read(
    ticket_id: UUID,
    data: TicketMessagesRead,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> SupportUnreadCount:
    return SupportUnreadCount(
        unread_count=await SupportService.mark_messages_read(
            session,
            ticket_id=ticket_id,
            message_ids=data.message_ids,
            user_id=admin.id,
            is_admin=True,
        )
    )


@router.get("/tickets", response_model=PaginationResponse[AdminTicketRead])
async def list_tickets(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[AdminTicketRead]:
    settings = get_settings()
    items, total = await SupportService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[AdminTicketRead.from_ticket(item, settings.api_prefix) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/tickets/{ticket_id}", response_model=AdminTicketRead)
async def get_ticket(
    ticket_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> AdminTicketRead:
    settings = get_settings()
    return AdminTicketRead.from_ticket(
        await SupportService.get_ticket_admin(session, ticket_id),
        settings.api_prefix,
    )


@router.post("/tickets/{ticket_id}/messages", response_model=MessageRead)
async def add_message(
    ticket_id: UUID,
    data: MessageCreate,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> MessageRead:
    settings = get_settings()
    message = await SupportService.add_message(
        session,
        ticket_id=ticket_id,
        author=admin,
        message=data.message,
        txid=data.txid,
        is_admin=True,
    )
    return MessageRead.from_message(message, settings.api_prefix)


@router.post("/tickets/{ticket_id}/status", response_model=AdminTicketRead)
async def update_status(
    ticket_id: UUID,
    data: TicketStatusUpdate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminTicketRead:
    settings = get_settings()
    ticket = await SupportService.update_status(
        session,
        ticket_id=ticket_id,
        status=data.status,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return AdminTicketRead.from_ticket(ticket, settings.api_prefix)


@router.post("/tickets/{ticket_id}/resolve-deposit", response_model=AdminTicketRead)
async def resolve_deposit(
    ticket_id: UUID,
    data: ResolveTicketDepositRequest,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> AdminTicketRead:
    settings = get_settings()
    ticket = await SupportService.resolve_deposit(
        session,
        ticket_id=ticket_id,
        invoice_id=data.invoice_id,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return AdminTicketRead.from_ticket(ticket, settings.api_prefix)
