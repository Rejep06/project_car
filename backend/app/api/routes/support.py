"""Пользовательское API обращений и защищённых вложений."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse

from app.api.dependencies import CurrentUserDep, SessionDep
from app.core.config import get_settings
from app.schemas.common import PaginationResponse
from app.schemas.support import (
    AttachmentRead,
    MessageCreate,
    MessageRead,
    TicketCreate,
    TicketRead,
)
from app.services.support_service import SupportService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/support", tags=["Поддержка"])


@router.post(
    "/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    data: TicketCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TicketRead:
    settings = get_settings()
    ticket = await SupportService.create_ticket(
        session,
        user=current_user,
        category=data.category,
        subject=data.subject,
        message=data.message,
        txid=data.txid,
        related_deposit_invoice_id=data.related_deposit_invoice_id,
    )
    return TicketRead.from_ticket(ticket, settings.api_prefix)


@router.get("/tickets", response_model=PaginationResponse[TicketRead])
async def list_tickets(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[TicketRead]:
    settings = get_settings()
    items, total = await SupportService.list_user(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[TicketRead.from_ticket(item, settings.api_prefix) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> TicketRead:
    settings = get_settings()
    ticket = await SupportService.get_ticket_user(
        session, user_id=current_user.id, ticket_id=ticket_id
    )
    return TicketRead.from_ticket(ticket, settings.api_prefix)


@router.post("/tickets/{ticket_id}/messages", response_model=MessageRead)
async def add_ticket_message(
    ticket_id: UUID,
    data: MessageCreate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> MessageRead:
    settings = get_settings()
    message = await SupportService.add_message(
        session,
        ticket_id=ticket_id,
        author=current_user,
        message=data.message,
        txid=data.txid,
        is_admin=False,
    )
    return MessageRead.from_message(message, settings.api_prefix)


@router.post(
    "/messages/{message_id}/attachments",
    response_model=list[AttachmentRead],
    status_code=status.HTTP_201_CREATED,
)
async def add_attachments(
    message_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
    files: Annotated[list[UploadFile], File(description="До 3 файлов")],
) -> list[AttachmentRead]:
    settings = get_settings()
    attachments = await SupportService.add_attachments(
        session,
        message_id=message_id,
        requester=current_user,
        files=files,
        settings=settings,
    )
    return [
        AttachmentRead.from_attachment(item, settings.api_prefix)
        for item in attachments
    ]


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> FileResponse:
    attachment, path = await SupportService.get_attachment(
        session, attachment_id=attachment_id, requester=current_user
    )
    return FileResponse(
        path=path,
        media_type=attachment.mime_type,
        filename=attachment.original_filename,
    )
