"""Публичные опубликованные новости."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.post import PostRead
from app.services.post_service import PostService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/posts", tags=["Новости"])


@router.get("", response_model=PaginationResponse[PostRead])
async def list_posts(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[PostRead]:
    items, total = await PostService.list_public(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[PostRead.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{slug}", response_model=PostRead)
async def get_post(slug: str, session: SessionDep) -> PostRead:
    return PostRead.model_validate(await PostService.get_public(session, slug))
