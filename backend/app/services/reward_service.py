"""Надёжная обработка просроченных reward payout без двойного начисления."""

import logging
from datetime import timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.enums import RewardPayoutStatus, WalletOperationType
from app.db.models import RewardPayout
from app.services.wallet_service import WalletService
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)


class RewardService:
    @staticmethod
    async def claim_due_payouts(
        session: AsyncSession, *, batch_size: int
    ) -> list[UUID]:
        """Захватывает порцию выплат через FOR UPDATE SKIP LOCKED."""
        now = utcnow()
        stale_before = now - timedelta(minutes=5)
        stmt = (
            select(RewardPayout)
            .where(
                RewardPayout.due_at <= now,
                or_(
                    RewardPayout.status.in_(
                        [RewardPayoutStatus.PENDING, RewardPayoutStatus.FAILED]
                    ),
                    (
                        (RewardPayout.status == RewardPayoutStatus.PROCESSING)
                        & (RewardPayout.updated_at <= stale_before)
                    ),
                ),
            )
            .order_by(RewardPayout.due_at)
            .with_for_update(skip_locked=True)
            .limit(batch_size)
        )
        payouts = list((await session.scalars(stmt)).all())
        for payout in payouts:
            payout.status = RewardPayoutStatus.PROCESSING
            payout.last_error = None
        await session.commit()
        return [payout.id for payout in payouts]

    @staticmethod
    async def process_one(session: AsyncSession, payout_id: UUID) -> bool:
        payout = await session.scalar(
            select(RewardPayout)
            .where(RewardPayout.id == payout_id)
            .with_for_update()
        )
        if payout is None or payout.status == RewardPayoutStatus.CANCELLED:
            return False
        if payout.status == RewardPayoutStatus.PAID:
            return False

        transaction, _ = await WalletService.apply_change(
            session,
            user_id=payout.user_id,
            operation_type=WalletOperationType.REWARD_CREDIT,
            available_delta_atomic=payout.amount_atomic,
            locked_delta_atomic=0,
            idempotency_key=f"reward:{payout.id}",
            related_entity_type="reward_payout",
            related_entity_id=payout.id,
            description="Начисление периодического вознаграждения",
            metadata_json={"user_subscription_id": str(payout.user_subscription_id)},
        )
        payout.wallet_transaction_id = transaction.id
        payout.status = RewardPayoutStatus.PAID
        payout.paid_at = utcnow()
        payout.last_error = None
        await session.commit()
        return True

    @staticmethod
    async def mark_failed(
        session: AsyncSession, payout_id: UUID, error: Exception
    ) -> None:
        payout = await session.scalar(
            select(RewardPayout)
            .where(RewardPayout.id == payout_id)
            .with_for_update()
        )
        if payout is None or payout.status == RewardPayoutStatus.PAID:
            return
        payout.status = RewardPayoutStatus.FAILED
        payout.attempt_count += 1
        payout.last_error = f"{type(error).__name__}: {error}"[:1000]
        await session.commit()

    @classmethod
    async def process_batch(
        cls,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        batch_size: int,
    ) -> int:
        async with session_factory() as claim_session:
            payout_ids = await cls.claim_due_payouts(
                claim_session, batch_size=batch_size
            )
        processed = 0
        for payout_id in payout_ids:
            try:
                async with session_factory() as session:
                    if await cls.process_one(session, payout_id):
                        processed += 1
            except Exception as exc:  # Процесс должен продолжить обработку следующих выплат
                logger.exception("Ошибка reward payout %s", payout_id)
                async with session_factory() as failure_session:
                    await cls.mark_failed(failure_session, payout_id, exc)
        return processed
