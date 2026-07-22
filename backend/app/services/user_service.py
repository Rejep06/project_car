"""Профиль пользователя и безопасные административные действия."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppError
from app.db.enums import WalletOperationType
from app.db.models import User
from app.services.audit_service import AuditService
from app.services.wallet_service import WalletService
from app.utils.money import format_amount, parse_amount


class UserService:
    @staticmethod
    async def update_me(session: AsyncSession, *, user_id: UUID, email: str) -> User:
        user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise AppError("user_not_found", "Пользователь не найден", status_code=404)
        user.email = email.strip().lower()
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError("email_already_exists", "Этот email уже используется", status_code=409) from exc
        await session.refresh(user)
        return user

    @staticmethod
    async def list_users(
        session: AsyncSession, *, offset: int, limit: int
    ) -> tuple[list[User], int]:
        items = list(
            (
                await session.scalars(
                    select(User)
                    .options(selectinload(User.wallet))
                    .order_by(User.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(await session.scalar(select(func.count()).select_from(User)) or 0)
        return items, total

    @staticmethod
    async def get_user(session: AsyncSession, user_id: UUID) -> User:
        user = await session.scalar(
            select(User).options(selectinload(User.wallet)).where(User.id == user_id)
        )
        if user is None:
            raise AppError("user_not_found", "Пользователь не найден", status_code=404)
        return user

    @staticmethod
    async def set_frozen(
        session: AsyncSession,
        *,
        user_id: UUID,
        is_frozen: bool,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> User:
        if user_id == admin_user_id:
            raise AppError("self_freeze_forbidden", "Нельзя заморозить собственную учётную запись", status_code=409)
        user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            raise AppError("user_not_found", "Пользователь не найден", status_code=404)
        old = {"is_frozen": user.is_frozen}
        user.is_frozen = is_frozen
        await AuditService.record(
            session,
            admin_user_id=admin_user_id,
            action="user_frozen" if is_frozen else "user_unfrozen",
            entity_type="user",
            entity_id=user.id,
            old_data=old,
            new_data={"is_frozen": is_frozen},
            ip_address=ip_address,
        )
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def adjust_balance(
        session: AsyncSession,
        *,
        user_id: UUID,
        amount: str,
        description: str,
        idempotency_key: str,
        admin_user_id: UUID,
        ip_address: str | None,
    ) -> User:
        amount_atomic = parse_amount(amount)
        transaction, created = await WalletService.apply_change(
            session,
            user_id=user_id,
            operation_type=WalletOperationType.ADMIN_ADJUSTMENT,
            available_delta_atomic=amount_atomic,
            locked_delta_atomic=0,
            idempotency_key=idempotency_key,
            related_entity_type="user",
            related_entity_id=user_id,
            description=description,
            metadata_json={"admin_user_id": str(admin_user_id)},
        )
        if created:
            await AuditService.record(
                session,
                admin_user_id=admin_user_id,
                action="balance_adjusted",
                entity_type="user",
                entity_id=user_id,
                new_data={
                    "amount": format_amount(amount_atomic),
                    "description": description,
                    "wallet_transaction_id": str(transaction.id),
                },
                ip_address=ip_address,
            )
        await session.commit()
        return await UserService.get_user(session, user_id)
