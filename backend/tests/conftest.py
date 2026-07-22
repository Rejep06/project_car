"""Изолированная БД, тестовый HTTP-клиент и фабрики данных."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

# Переменные устанавливаются до первого импорта app.db.session.
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:////tmp/subscription_platform_test.db",
)
os.environ["JWT_SECRET"] = "test-secret-that-is-not-used-in-production"
os.environ["NETWORK"] = "TRON"
os.environ["NETWORK_DISPLAY_NAME"] = "TRON (TRC20)"
os.environ["ASSET"] = "USDT"
os.environ["BINANCE_ENABLED"] = "false"
os.environ["BINANCE_DEPOSIT_ADDRESS"] = "T" + "A" * 33
os.environ["SUPPORT_UPLOAD_DIR"] = "/tmp/subscription_platform_test_uploads"
os.environ["MIN_DEPOSIT_AMOUNT"] = "10.000000"
os.environ["MIN_WITHDRAWAL_AMOUNT"] = "20.000000"
os.environ["WITHDRAWAL_FEE"] = "2.000000"

import httpx
import pytest_asyncio
from sqlalchemy import event

from app.core.security import hash_password
from app.db.base import Base
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import async_session_maker, engine
from app.main import app
from app.services.wallet_service import WalletService

UPLOAD_DIR = Path(os.environ["SUPPORT_UPLOAD_DIR"])


if engine.sync_engine.dialect.name == "sqlite":

    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


@pytest_asyncio.fixture
async def client():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def make_account(client):
    async def factory(email: str | None = None, password: str = "User123!") -> dict:
        email = email or f"user-{uuid4().hex[:8]}@example.com"
        response = await client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        assert response.status_code == 201, response.text
        login = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert login.status_code == 200, login.text
        me = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        return {
            "id": me.json()["id"],
            "email": email,
            "password": password,
            "access_token": login.json()["access_token"],
            "refresh_token": login.json()["refresh_token"],
            "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
        }

    return factory


@pytest_asyncio.fixture
async def admin_account(client):
    email = "admin@example.com"
    password = "Admin123!"
    async with async_session_maker() as session:
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_frozen=False,
        )
        session.add(user)
        await session.flush()
        await WalletService.create_wallet(session, user.id)
        await session.commit()
        user_id = str(user.id)
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text
    return {
        "id": user_id,
        "email": email,
        "password": password,
        "access_token": login.json()["access_token"],
        "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
    }


@pytest_asyncio.fixture
async def create_plan(client, admin_account):
    async def factory(**overrides) -> dict:
        suffix = uuid4().hex[:8]
        payload = {
            "title": "Игровая подписка",
            "slug": f"game-plan-{suffix}",
            "category": "game",
            "short_description": "Короткое описание",
            "full_description": "Полное описание тарифа",
            "image_url": None,
            "price": "10.000000",
            "access_duration_value": 1,
            "access_duration_unit": "month",
            "reward_amount": "1.000000",
            "reward_frequency": "daily",
            "reward_duration_value": 2,
            "reward_duration_unit": "day",
            "is_active": True,
        }
        payload.update(overrides)
        response = await client.post(
            "/api/v1/admin/plans", json=payload, headers=admin_account["headers"]
        )
        assert response.status_code == 201, response.text
        return response.json()

    return factory


@pytest_asyncio.fixture
async def credit_balance(client, admin_account):
    async def factory(account: dict, amount: str = "100.000000") -> dict:
        headers = {
            **admin_account["headers"],
            "Idempotency-Key": f"test-credit-{uuid4()}",
        }
        response = await client.post(
            f"/api/v1/admin/users/{account['id']}/balance-adjustment",
            json={"amount": amount, "description": "Тестовое пополнение"},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        return response.json()

    return factory
