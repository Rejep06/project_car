"""Только чтение неизменяемого аудита."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import CurrentAdminDep, SessionDep
from app.schemas.admin import AuditLogRead
from app.schemas.common import PaginationResponse
from app.services.audit_service import AuditService
from app.utils.pagination import PaginationParams, get_pagination

router = APIRouter(prefix="/admin/audit-logs", tags=["Администратор: аудит"])


@router.get("", response_model=PaginationResponse[AuditLogRead])
async def list_audit_logs(
    session: SessionDep,
    _: CurrentAdminDep,
    pagination: Annotated[PaginationParams, Depends(get_pagination)],
) -> PaginationResponse[AuditLogRead]:
    items, total = await AuditService.list_logs(
        session, offset=pagination.offset, limit=pagination.page_size
    )
    return PaginationResponse(
        items=[AuditLogRead.model_validate(item) for item in items],
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )
