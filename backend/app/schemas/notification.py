"""Схемы уведомлений личного кабинета."""

from datetime import datetime
from uuid import UUID

from app.db.enums import NotificationType
from app.schemas.common import APIModel


class NotificationRead(APIModel):
    id: UUID
    notification_type: NotificationType
    title: str
    message: str
    action_url: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class NotificationCount(APIModel):
    unread_count: int
