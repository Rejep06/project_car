"""Запись неизменяемого аудита административных действий."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


class AuditService:
    @staticmethod
    async def record(
        session: AsyncSession,
        *,
        admin_user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID | None,
        old_data: dict[str, Any] | None = None,
        new_data: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            admin_user_id=admin_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_data=old_data,
            new_data=new_data,
            ip_address=ip_address,
        )
        session.add(entry)
        await session.flush()
        return entry

    @staticmethod
    async def list_logs(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[AuditLog], int]:
        items = list(
            (
                await session.scalars(
                    select(AuditLog)
                    .order_by(AuditLog.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(await session.scalar(select(func.count()).select_from(AuditLog)) or 0)
        return items, total
