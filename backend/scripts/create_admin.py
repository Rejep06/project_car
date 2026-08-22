"""Интерактивное создание администратора без хранения пароля в коде."""

import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import async_session_maker
from app.services.wallet_service import WalletService
from app.utils.datetime import utcnow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Создать администратора")
    parser.add_argument("--email", help="Email администратора")
    return parser.parse_args()


async def create_admin(email: str, password: str) -> None:
    normalized_email = email.strip().lower()
    async with async_session_maker() as session:
        existing = await session.scalar(select(User).where(User.email == normalized_email))
        if existing is not None:
            raise RuntimeError("Пользователь с таким email уже существует")
        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_frozen=False,
            email_verified_at=utcnow(),
        )
        session.add(user)
        await session.flush()
        await WalletService.create_wallet(session, user.id)
        await session.commit()
        print(f"Администратор создан: {normalized_email}")


def main() -> None:
    args = parse_args()
    email = args.email or os.getenv("ADMIN_EMAIL") or input("Email администратора: ").strip()
    password = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Пароль (минимум 8 символов): ")
    if len(password) < 8:
        raise RuntimeError("Пароль должен содержать минимум 8 символов")
    asyncio.run(create_admin(email, password))


if __name__ == "__main__":
    main()
