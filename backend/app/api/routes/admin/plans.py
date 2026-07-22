"""Административное управление тарифами."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.common import PaginationResponse
from app.schemas.plan import PlanCreate, PlanRead, PlanUpdate
from app.services.plan_service import PlanService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/plans", tags=["Администратор: тарифы"])


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: PlanCreate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> PlanRead:
    plan = await PlanService.create(
        session,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return PlanRead.from_plan(plan)


@router.get("", response_model=PaginationResponse[PlanRead])
async def list_plans(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[PlanRead]:
    items, total = await PlanService.list_admin(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[PlanRead.from_plan(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


@router.get("/{plan_id}", response_model=PlanRead)
async def get_plan(
    plan_id: UUID, session: SessionDep, _: CurrentAdminDep
) -> PlanRead:
    return PlanRead.from_plan(await PlanService.get_admin(session, plan_id))


@router.patch("/{plan_id}", response_model=PlanRead)
async def update_plan(
    plan_id: UUID,
    data: PlanUpdate,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> PlanRead:
    plan = await PlanService.update(
        session,
        plan_id=plan_id,
        data=data,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return PlanRead.from_plan(plan)


@router.post("/{plan_id}/activate", response_model=PlanRead)
async def activate_plan(
    plan_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> PlanRead:
    plan = await PlanService.set_active(
        session,
        plan_id=plan_id,
        is_active=True,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return PlanRead.from_plan(plan)


@router.post("/{plan_id}/deactivate", response_model=PlanRead)
async def deactivate_plan(
    plan_id: UUID,
    request: Request,
    session: SessionDep,
    admin: CurrentAdminDep,
) -> PlanRead:
    plan = await PlanService.set_active(
        session,
        plan_id=plan_id,
        is_active=False,
        admin_user_id=admin.id,
        ip_address=client_ip(request),
    )
    return PlanRead.from_plan(plan)
