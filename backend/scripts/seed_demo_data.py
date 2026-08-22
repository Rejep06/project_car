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
    PlanTier,
    PostStatus,
    RewardFrequency,
    UserRole,
    WalletOperationType,
)
from app.db.models import Post, SubscriptionPlan, User
from app.db.session import async_session_maker
from app.services.deposit_wallet_service import DepositWalletService
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
        email_verified_at=utcnow(),
    )
    session.add(user)
    await session.flush()
    await WalletService.create_wallet(session, user.id)
    return user


PROGRAMS = (
    {
        "tier": PlanTier.STARTER,
        "title": "Старт Драйв",
        "short_description": "Базовая клиентская программа для первого знакомства с условиями и регулярными вознаграждениями.",
        "full_description": "Доступный стартовый формат с понятной стоимостью, сроком участия и заранее опубликованным графиком вознаграждений.",
        "price": "50.000000",
        "reward": "1.000000",
        "frequency": RewardFrequency.WEEKLY,
    },
    {
        "tier": PlanTier.STANDARD,
        "title": "Драйв Плюс",
        "short_description": "Сбалансированная программа с расширенным сроком и увеличенным размером вознаграждений.",
        "full_description": "Основной вариант для клиентов, которым важны удобный срок программы и более высокий размер плановых начислений.",
        "price": "150.000000",
        "reward": "4.000000",
        "frequency": RewardFrequency.WEEKLY,
    },
    {
        "tier": PlanTier.PREMIUM,
        "title": "Премиум Драйв",
        "short_description": "Максимальный уровень программы с повышенными вознаграждениями и премиальными реферальными условиями.",
        "full_description": "Премиальный формат клиентской программы. Пригласивший пользователь дополнительно получает 2 USDT при каждом вознаграждении приглашённого участника этой программы.",
        "price": "300.000000",
        "reward": "10.000000",
        "frequency": RewardFrequency.WEEKLY,
    },
)


async def ensure_programs(session) -> None:
    for item in PROGRAMS:
        plan = await session.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.tier == item["tier"])
        )
        values = {
            "title": item["title"],
            "tier": item["tier"],
            "short_description": item["short_description"],
            "full_description": item["full_description"],
            "image_url": "/assets/program-car-photo.jpg",
            "price_atomic": parse_amount(item["price"]),
            "access_duration_value": 3,
            "access_duration_unit": DurationUnit.MONTH,
            "reward_amount_atomic": parse_amount(item["reward"]),
            "reward_frequency": item["frequency"],
            "reward_duration_value": 3,
            "reward_duration_unit": DurationUnit.MONTH,
            "is_active": True,
        }
        if plan is None:
            session.add(SubscriptionPlan(**values))
        else:
            for field, value in values.items():
                setattr(plan, field, value)


async def ensure_wallet(session) -> None:
    await DepositWalletService.ensure_default_wallet(session, get_settings())


async def ensure_posts(session, admin: User) -> None:
    posts = (
        {
            "slug": "company-since-2023",
            "title": "Работаем для клиентов с 2023 года",
            "excerpt": "Развиваем автомобильные клиентские программы и делаем условия участия понятными и доступными.",
            "content": "С 2023 года компания развивает клиентские программы, помогает участникам получать дополнительные вознаграждения и последовательно расширяет автомобильное направление.",
        },
        {
            "slug": "three-program-levels",
            "title": "Три уровня клиентских программ",
            "excerpt": "Старт Драйв, Драйв Плюс и Премиум Драйв — выберите подходящий формат участия.",
            "content": "Каждая программа имеет собственное название, описание, стоимость, срок и график вознаграждений. Актуальные условия всегда доступны в каталоге программ.",
        },
    )
    for item in posts:
        post = await session.scalar(select(Post).where(Post.slug == item["slug"]))
        if post is None:
            session.add(
                Post(
                    author_id=admin.id,
                    title=item["title"],
                    slug=item["slug"],
                    excerpt=item["excerpt"],
                    content=item["content"],
                    status=PostStatus.PUBLISHED,
                    published_at=utcnow(),
                )
            )


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
        await ensure_programs(session)
        await ensure_wallet(session)
        await ensure_posts(session, admin)
        await session.commit()
        print(
            "Demo data создана: admin@example.com / Admin123!, "
            "user@example.com / User123!"
        )


if __name__ == "__main__":
    asyncio.run(seed())
