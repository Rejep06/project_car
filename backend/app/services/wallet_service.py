"""Единственная точка изменения внутреннего баланса."""

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.db.enums import WalletOperationType
from app.db.models import Wallet, WalletTransaction
from app.utils.money import MAX_ATOMIC


class WalletService:
    """Изменяет available/locked только под SELECT FOR UPDATE и с журналом."""

    @staticmethod
    async def create_wallet(session: AsyncSession, user_id: UUID) -> Wallet:
        settings = get_settings()
        wallet = Wallet(user_id=user_id, asset=settings.asset, available_balance_atomic=0, locked_balance_atomic=0)
        session.add(wallet)
        await session.flush()
        return wallet

    @staticmethod
    async def get_wallet(session: AsyncSession, user_id: UUID) -> Wallet:
        wallet = await session.scalar(select(Wallet).where(Wallet.user_id == user_id))
        if wallet is None:
            raise AppError("wallet_not_found", "Кошелёк не найден", status_code=404)
        return wallet

    @staticmethod
    async def lock_wallet(session: AsyncSession, user_id: UUID) -> Wallet:
        wallet = await session.scalar(
            select(Wallet).where(Wallet.user_id == user_id).with_for_update(of=Wallet)
        )
        if wallet is None:
            raise AppError("wallet_not_found", "Кошелёк не найден", status_code=404)
        return wallet

    @staticmethod
    async def find_transaction(
        session: AsyncSession, idempotency_key: str
    ) -> WalletTransaction | None:
        return await session.scalar(
            select(WalletTransaction).where(
                WalletTransaction.idempotency_key == idempotency_key
            )
        )

    @classmethod
    async def apply_change(
        cls,
        session: AsyncSession,
        *,
        user_id: UUID,
        operation_type: WalletOperationType,
        available_delta_atomic: int,
        locked_delta_atomic: int,
        idempotency_key: str,
        related_entity_type: str | None = None,
        related_entity_id: UUID | None = None,
        description: str = "",
        metadata_json: dict[str, Any] | None = None,
        locked_wallet: Wallet | None = None,
    ) -> tuple[WalletTransaction, bool]:
        """Применяет изменение и возвращает (transaction, создана_ли_операция)."""
        if not idempotency_key or len(idempotency_key) > 255:
            raise AppError("invalid_idempotency_key", "Некорректный idempotency key")

        wallet = locked_wallet or await cls.lock_wallet(session, user_id)
        if wallet.user_id != user_id:
            raise AppError("wallet_owner_mismatch", "Кошелёк принадлежит другому пользователю", status_code=409)

        existing = await cls.find_transaction(session, idempotency_key)
        if existing is not None:
            same_operation = (
                existing.wallet_id == wallet.id
                and existing.operation_type == operation_type
                and existing.available_delta_atomic == available_delta_atomic
                and existing.locked_delta_atomic == locked_delta_atomic
                and existing.related_entity_type == related_entity_type
                and existing.related_entity_id == related_entity_id
            )
            if not same_operation:
                raise AppError(
                    "idempotency_key_conflict",
                    "Idempotency key уже использован для другой операции",
                    status_code=409,
                )
            return existing, False

        available_after = wallet.available_balance_atomic + available_delta_atomic
        locked_after = wallet.locked_balance_atomic + locked_delta_atomic
        if available_after < 0:
            raise AppError(
                "insufficient_balance",
                "Недостаточно средств",
                status_code=409,
            )
        if locked_after < 0:
            raise AppError(
                "insufficient_locked_balance",
                "Недостаточно заблокированных средств",
                status_code=409,
            )
        if available_after > MAX_ATOMIC or locked_after > MAX_ATOMIC:
            raise AppError(
                "balance_overflow",
                "Баланс превышает допустимый диапазон",
                status_code=409,
            )

        wallet.available_balance_atomic = available_after
        wallet.locked_balance_atomic = locked_after
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            operation_type=operation_type,
            available_delta_atomic=available_delta_atomic,
            locked_delta_atomic=locked_delta_atomic,
            available_after_atomic=available_after,
            locked_after_atomic=locked_after,
            idempotency_key=idempotency_key,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            description=description,
            metadata_json=metadata_json or {},
        )
        session.add(transaction)
        await session.flush()
        return transaction, True

    @staticmethod
    async def list_transactions(
        session: AsyncSession, *, user_id: UUID, offset: int, limit: int
    ) -> tuple[list[WalletTransaction], int]:
        wallet = await WalletService.get_wallet(session, user_id)
        condition = WalletTransaction.wallet_id == wallet.id
        items = list(
            (
                await session.scalars(
                    select(WalletTransaction)
                    .where(condition)
                    .order_by(WalletTransaction.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(WalletTransaction).where(condition)
            )
            or 0
        )
        return items, total
