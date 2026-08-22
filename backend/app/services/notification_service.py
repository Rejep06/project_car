"""Создание и чтение уведомлений личного кабинета."""

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.enums import NotificationType
from app.db.models import UserNotification
from app.utils.datetime import utcnow


class NotificationService:
    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        action_url: str | None = None,
    ) -> UserNotification:
        item = UserNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            is_read=False,
        )
        session.add(item)
        await session.flush()
        return item

    @staticmethod
    async def list_user(
        session: AsyncSession, *, user_id: UUID, offset: int, limit: int
    ) -> tuple[list[UserNotification], int]:
        condition = UserNotification.user_id == user_id
        items = list(
            (
                await session.scalars(
                    select(UserNotification)
                    .where(condition)
                    .order_by(UserNotification.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(UserNotification).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def unread_count(session: AsyncSession, *, user_id: UUID) -> int:
        return int(
            await session.scalar(
                select(func.count())
                .select_from(UserNotification)
                .where(
                    UserNotification.user_id == user_id,
                    UserNotification.is_read.is_(False),
                )
            )
            or 0
        )

    @staticmethod
    async def mark_read(
        session: AsyncSession, *, user_id: UUID, notification_id: UUID
    ) -> UserNotification:
        item = await session.scalar(
            select(UserNotification)
            .where(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            )
            .with_for_update(of=UserNotification)
        )
        if item is None:
            raise AppError(
                "notification_not_found", "Уведомление не найдено", status_code=404
            )
        if not item.is_read:
            item.is_read = True
            item.read_at = utcnow()
            await session.commit()
            await session.refresh(item)
        return item

    @staticmethod
    async def mark_all_read(session: AsyncSession, *, user_id: UUID) -> int:
        result = await session.execute(
            update(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.is_read.is_(False),
            )
            .values(is_read=True, read_at=utcnow())
        )
        await session.commit()
        return int(result.rowcount or 0)
