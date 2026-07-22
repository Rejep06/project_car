"""Неизменяемый аудит действий администратора."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base
from app.utils.datetime import utcnow


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    admin_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    old_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow, server_default=func.now(), index=True, nullable=False
    )

    admin_user = relationship("User", lazy="joined")


@event.listens_for(AuditLog, "before_update")
def prevent_audit_update(*_: object) -> None:
    raise RuntimeError("AuditLog является неизменяемой записью")


@event.listens_for(AuditLog, "before_delete")
def prevent_audit_delete(*_: object) -> None:
    raise RuntimeError("AuditLog нельзя удалять")
