"""Уведомления текущего пользователя."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentUserDep, SessionDep
from app.schemas.common import MessageResponse, PaginationResponse
from app.schemas.notification import NotificationCount, NotificationRead
from app.services.notification_service import NotificationService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/notifications", tags=["Уведомления"])


@router.get("", response_model=PaginationResponse[NotificationRead])
async def list_notifications(
    session: SessionDep,
    current_user: CurrentUserDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[NotificationRead]:
    items, total = await NotificationService.list_user(
        session,
        user_id=current_user.id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return PaginationResponse(
        items=[NotificationRead.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/unread-count", response_model=NotificationCount)
async def unread_count(
    session: SessionDep, current_user: CurrentUserDep
) -> NotificationCount:
    return NotificationCount(
        unread_count=await NotificationService.unread_count(
            session, user_id=current_user.id
        )
    )


@router.post("/read-all", response_model=MessageResponse)
async def mark_all_read(
    session: SessionDep, current_user: CurrentUserDep
) -> MessageResponse:
    count = await NotificationService.mark_all_read(
        session, user_id=current_user.id
    )
    return MessageResponse(message=f"Прочитано уведомлений: {count}")


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_read(
    notification_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> NotificationRead:
    return NotificationRead.model_validate(
        await NotificationService.mark_read(
            session,
            user_id=current_user.id,
            notification_id=notification_id,
        )
    )
