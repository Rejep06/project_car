"""Схемы административного аудита."""

from datetime import datetime
from typing import Any
from uuid import UUID

from app.schemas.common import APIModel


class AuditLogRead(APIModel):
    id: UUID
    admin_user_id: UUID
    action: str
    entity_type: str
    entity_id: UUID | None
    old_data: dict[str, Any] | None
    new_data: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime
