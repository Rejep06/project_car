"""Демонстрационные данные только для development-окружения."""

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.enums import (
    DurationUnit,
    PlanCategory,
    PostStatus,
    RewardFrequency,
    UserRole,
    WalletOperationType,
)
from app.db.models import Post, SubscriptionPlan, User
from app.db.session import async_session_maker
from app.services.wallet_service import WalletService
from app.utils.datetime import utcnow
from app.utils.money import parse_amount


async def ensure_user(session, email: str, password: str, role: UserRole) -> User:
    user = await session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        is_frozen=False,
    )
    session.add(user)
    await session.flush()
    await WalletService.create_wallet(session, user.id)
    return user


async def seed() -> None:
    settings = get_settings()
    if settings.app_env != "development":
        raise RuntimeError("seed_demo_data.py разрешён только при APP_ENV=development")
    async with async_session_maker() as session:
        admin = await ensure_user(
            session, "admin@example.com", "Admin123!", UserRole.ADMIN
        )
        user = await ensure_user(
            session, "user@example.com", "User123!", UserRole.USER
        )
        await WalletService.apply_change(
            session,
            user_id=user.id,
            operation_type=WalletOperationType.ADMIN_ADJUSTMENT,
            available_delta_atomic=parse_amount("500.000000"),
            locked_delta_atomic=0,
            idempotency_key="demo:initial-balance:user@example.com",
            related_entity_type="user",
            related_entity_id=user.id,
            description="Демонстрационный баланс",
        )

        plan = await session.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.slug == "demo-game")
        )
        if plan is None:
            session.add(
                SubscriptionPlan(
                    title="Демонстрационная игровая подписка",
                    slug="demo-game",
                    category=PlanCategory.GAME,
                    short_description="Тариф для знакомства с API",
                    full_description="Не предназначен для production.",
                    price_atomic=parse_amount("50.000000"),
                    access_duration_value=1,
                    access_duration_unit=DurationUnit.MONTH,
                    reward_amount_atomic=parse_amount("1.000000"),
                    reward_frequency=RewardFrequency.WEEKLY,
                    reward_duration_value=1,
                    reward_duration_unit=DurationUnit.MONTH,
                    is_active=True,
                )
            )
        post = await session.scalar(select(Post).where(Post.slug == "demo-news"))
        if post is None:
            session.add(
                Post(
                    author_id=admin.id,
                    title="Демонстрационная новость",
                    slug="demo-news",
                    excerpt="Проверка публичного API новостей.",
                    content="Эта запись создана скриптом seed_demo_data.py.",
                    status=PostStatus.PUBLISHED,
                    published_at=utcnow(),
                )
            )
        await session.commit()
        print("Demo data создана: admin@example.com / Admin123!, user@example.com / User123!")


if __name__ == "__main__":
    asyncio.run(seed())
