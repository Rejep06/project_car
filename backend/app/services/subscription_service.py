"""Атомарная покупка подписки и создание полного графика выплат."""

from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import AppError
from app.db.enums import RewardPayoutStatus, UserSubscriptionStatus, WalletOperationType
from app.db.models import RewardPayout, SubscriptionPlan, User, UserSubscription
from app.services.wallet_service import WalletService
from app.utils.datetime import add_duration, add_reward_frequency, utcnow

MAX_REWARD_PAYOUTS_PER_SUBSCRIPTION = 5000


class SubscriptionService:
    @staticmethod
    async def expire_subscriptions(
        session: AsyncSession, *, user_id: UUID | None = None
    ) -> int:
        """Лениво помечает завершившийся доступ статусом expired."""
        conditions = [
            UserSubscription.status == UserSubscriptionStatus.ACTIVE,
            UserSubscription.access_ends_at <= utcnow(),
        ]
        if user_id is not None:
            conditions.append(UserSubscription.user_id == user_id)
        result = await session.execute(
            update(UserSubscription)
            .where(*conditions)
            .values(status=UserSubscriptionStatus.EXPIRED)
        )
        await session.flush()
        return int(result.rowcount or 0)

    @staticmethod
    def build_reward_schedule(subscription: UserSubscription) -> list[RewardPayout]:
        """Создаёт календарный график; месяц рассчитывается через relativedelta."""
        if subscription.reward_amount_atomic <= 0:
            return []
        reward_ends_at = add_duration(
            subscription.purchased_at,
            subscription.reward_duration_value,
            subscription.reward_duration_unit.value,
        )
        due_at = add_reward_frequency(
            subscription.purchased_at, subscription.reward_frequency.value
        )
        payouts: list[RewardPayout] = []
        while due_at <= reward_ends_at:
            if len(payouts) >= MAX_REWARD_PAYOUTS_PER_SUBSCRIPTION:
                raise AppError(
                    "reward_schedule_too_large",
                    "График вознаграждений превышает безопасный лимит",
                    status_code=409,
                )
            payouts.append(
                RewardPayout(
                    user_subscription_id=subscription.id,
                    user_id=subscription.user_id,
                    amount_atomic=subscription.reward_amount_atomic,
                    due_at=due_at,
                    status=RewardPayoutStatus.PENDING,
                    attempt_count=0,
                )
            )
            due_at = add_reward_frequency(due_at, subscription.reward_frequency.value)
        return payouts

    @staticmethod
    async def purchase(
        session: AsyncSession,
        *,
        user: User,
        plan_id: UUID,
        idempotency_key: str,
    ) -> tuple[UserSubscription, list[RewardPayout], bool]:
        if user.is_frozen:
            raise AppError(
                "user_frozen",
                "Операции пользователя заморожены",
                status_code=403,
            )

        # Блокировка кошелька сериализует конкурирующие покупки пользователя.
        wallet = await WalletService.lock_wallet(session, user.id)
        existing_transaction = await WalletService.find_transaction(
            session, idempotency_key
        )
        if existing_transaction is not None:
            metadata_plan_id = (existing_transaction.metadata_json or {}).get(
                "plan_id"
            )
            if (
                existing_transaction.wallet_id != wallet.id
                or existing_transaction.operation_type
                != WalletOperationType.SUBSCRIPTION_PURCHASE
                or existing_transaction.related_entity_type != "user_subscription"
                or existing_transaction.related_entity_id is None
                or metadata_plan_id != str(plan_id)
            ):
                raise AppError(
                    "idempotency_key_conflict",
                    "Idempotency key уже использован для другой операции",
                    status_code=409,
                )
            existing = await session.scalar(
                select(UserSubscription)
                .options(joinedload(UserSubscription.plan))
                .where(
                    UserSubscription.id
                    == existing_transaction.related_entity_id,
                    UserSubscription.user_id == user.id,
                    UserSubscription.plan_id == plan_id,
                )
            )
            if existing is None:
                raise AppError(
                    "idempotency_state_error",
                    "Не удалось восстановить результат предыдущей покупки",
                    status_code=409,
                )
            payouts = list(
                (
                    await session.scalars(
                        select(RewardPayout)
                        .where(
                            RewardPayout.user_subscription_id == existing.id
                        )
                        .order_by(RewardPayout.due_at)
                    )
                ).all()
            )
            return existing, payouts, False

        plan = await session.scalar(
            select(SubscriptionPlan).where(
                SubscriptionPlan.id == plan_id,
                SubscriptionPlan.is_active.is_(True),
            )
        )
        if plan is None:
            raise AppError(
                "plan_not_found",
                "Активный тариф не найден",
                status_code=404,
            )

        now = utcnow()
        subscription = UserSubscription(
            id=uuid4(),
            user_id=user.id,
            plan_id=plan.id,
            status=UserSubscriptionStatus.ACTIVE,
            purchased_at=now,
            access_started_at=now,
            access_ends_at=add_duration(
                now,
                plan.access_duration_value,
                plan.access_duration_unit.value,
            ),
            price_atomic=plan.price_atomic,
            reward_amount_atomic=plan.reward_amount_atomic,
            reward_frequency=plan.reward_frequency,
            reward_duration_value=plan.reward_duration_value,
            reward_duration_unit=plan.reward_duration_unit,
        )

        await WalletService.apply_change(
            session,
            user_id=user.id,
            operation_type=WalletOperationType.SUBSCRIPTION_PURCHASE,
            available_delta_atomic=-plan.price_atomic,
            locked_delta_atomic=0,
            idempotency_key=idempotency_key,
            related_entity_type="user_subscription",
            related_entity_id=subscription.id,
            description=f"Покупка подписки: {plan.title}",
            metadata_json={"plan_id": str(plan.id)},
            locked_wallet=wallet,
        )
        session.add(subscription)
        payouts = SubscriptionService.build_reward_schedule(subscription)
        session.add_all(payouts)
        await session.commit()

        result = await session.scalar(
            select(UserSubscription)
            .options(joinedload(UserSubscription.plan))
            .where(UserSubscription.id == subscription.id)
        )
        assert result is not None
        return result, payouts, True

    @staticmethod
    async def list_user(
        session: AsyncSession,
        *,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> tuple[list[UserSubscription], int]:
        await SubscriptionService.expire_subscriptions(session, user_id=user_id)
        await session.commit()
        condition = UserSubscription.user_id == user_id
        items = list(
            (
                await session.scalars(
                    select(UserSubscription)
                    .options(joinedload(UserSubscription.plan))
                    .where(condition)
                    .order_by(UserSubscription.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
            ).unique().all()
        )
        total = int(
            await session.scalar(
                select(func.count()).select_from(UserSubscription).where(condition)
            )
            or 0
        )
        return items, total

    @staticmethod
    async def get_user_subscription(
        session: AsyncSession, *, user_id: UUID, subscription_id: UUID
    ) -> tuple[UserSubscription, list[RewardPayout]]:
        await SubscriptionService.expire_subscriptions(session, user_id=user_id)
        await session.commit()
        subscription = await session.scalar(
            select(UserSubscription)
            .options(joinedload(UserSubscription.plan))
            .where(
                UserSubscription.id == subscription_id,
                UserSubscription.user_id == user_id,
            )
        )
        if subscription is None:
            raise AppError("subscription_not_found", "Подписка не найдена", status_code=404)
        payouts = list(
            (
                await session.scalars(
                    select(RewardPayout)
                    .where(RewardPayout.user_subscription_id == subscription.id)
                    .order_by(RewardPayout.due_at)
                )
            ).all()
        )
        return subscription, payouts
