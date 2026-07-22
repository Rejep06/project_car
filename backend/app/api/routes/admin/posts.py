"""Административное управление новостями."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.post import PostCreate, PostRead, PostUpdate
from app.services.post_service import PostService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/posts", tags=["Администратор: новости"])


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    data: PostCreate, session: SessionDep, admin: CurrentAdminDep
) -> PostRead:
    return PostRead.model_validate(
        await PostService.create(session, data=data, author_id=admin.id)
    )


@router.get("", response_model=PaginationResponse[PostRead])
async def list_posts(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[PostRead]:
    items, total = await PostService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[PostRead.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{post_id}", response_model=PostRead)
async def get_post(
    post_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> PostRead:
    return PostRead.model_validate(await PostService.get_admin(session, post_id))


@router.patch("/{post_id}", response_model=PostRead)
async def update_post(
    post_id: UUID,
    data: PostUpdate,
    session: SessionDep,
    _: CurrentAdminDep,
) -> PostRead:
    return PostRead.model_validate(
        await PostService.update(session, post_id=post_id, data=data)
    )


@router.post("/{post_id}/publish", response_model=PostRead)
async def publish_post(
    post_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> PostRead:
    return PostRead.model_validate(await PostService.publish(session, post_id))


@router.post("/{post_id}/archive", response_model=PostRead)
async def archive_post(
    post_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> PostRead:
    return PostRead.model_validate(await PostService.archive(session, post_id))
