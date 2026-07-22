"""Публичный каталог активных подписок."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.plan import PlanRead
from app.services.plan_service import PlanService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/plans", tags=["Тарифы"])


@router.get("", response_model=PaginationResponse[PlanRead])
async def list_plans(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[PlanRead]:
    items, total = await PlanService.list_public(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[PlanRead.from_plan(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{slug}", response_model=PlanRead)
async def get_plan(slug: str, session: SessionDep) -> PlanRead:
    return PlanRead.from_plan(await PlanService.get_public_by_slug(session, slug))
