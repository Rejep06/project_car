"""Регистрация, вход, ротация refresh token и logout."""

import hmac
from datetime import timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    TokenValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.enums import UserRole
from app.db.models import AuthSession, User
from app.schemas.auth import TokenPairResponse
from app.services.wallet_service import WalletService
from app.utils.datetime import ensure_utc, utcnow


class AuthService:
    @staticmethod
    async def register(session: AsyncSession, *, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        existing = await session.scalar(select(User.id).where(User.email == normalized_email))
        if existing is not None:
            raise AppError("email_already_exists", "Пользователь с таким email уже существует", status_code=409)

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            role=UserRole.USER,
            is_active=True,
            is_frozen=False,
        )
        session.add(user)
        try:
            await session.flush()
            await WalletService.create_wallet(session, user.id)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise AppError(
                "email_already_exists",
                "Пользователь с таким email уже существует",
                status_code=409,
            ) from exc
        await session.refresh(user)
        return user

    @staticmethod
    async def login(session: AsyncSession, *, email: str, password: str) -> TokenPairResponse:
        normalized_email = email.strip().lower()
        user = await session.scalar(select(User).where(User.email == normalized_email))
        if user is None or not verify_password(password, user.password_hash):
            raise AppError("invalid_credentials", "Неверный email или пароль", status_code=401)
        if not user.is_active:
            raise AppError("user_inactive", "Пользователь деактивирован", status_code=403)

        settings = get_settings()
        auth_session = AuthSession(
            id=uuid4(),
            user_id=user.id,
            refresh_token_hash="pending",
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
        refresh_token = create_refresh_token(user.id, auth_session.id)
        auth_session.refresh_token_hash = hash_refresh_token(refresh_token)
        session.add(auth_session)
        await session.commit()

        access_token, expires_in = create_access_token(user.id, user.role.value)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    async def refresh(session: AsyncSession, refresh_token: str) -> TokenPairResponse:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
        except (TokenValidationError, KeyError, ValueError) as exc:
            raise AppError("invalid_refresh_token", "Недействительный refresh token", status_code=401) from exc

        auth_session = await session.scalar(
            select(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
            .with_for_update()
        )
        if auth_session is None or auth_session.revoked_at is not None:
            raise AppError("invalid_refresh_token", "Refresh token отозван", status_code=401)
        if ensure_utc(auth_session.expires_at) <= utcnow():
            raise AppError("refresh_token_expired", "Refresh token истёк", status_code=401)
        candidate_hash = hash_refresh_token(refresh_token)
        if not hmac.compare_digest(auth_session.refresh_token_hash, candidate_hash):
            raise AppError("invalid_refresh_token", "Недействительный refresh token", status_code=401)

        user = await session.get(User, user_id)
        if user is None or not user.is_active:
            raise AppError("user_inactive", "Пользователь недоступен", status_code=403)

        new_refresh_token = create_refresh_token(user.id, auth_session.id)
        auth_session.refresh_token_hash = hash_refresh_token(new_refresh_token)
        await session.commit()
        access_token, expires_in = create_access_token(user.id, user.role.value)
        return TokenPairResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    async def logout(session: AsyncSession, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, "refresh")
            user_id = UUID(payload["sub"])
            session_id = UUID(payload["sid"])
        except (TokenValidationError, KeyError, ValueError) as exc:
            raise AppError("invalid_refresh_token", "Недействительный refresh token", status_code=401) from exc

        auth_session = await session.scalar(
            select(AuthSession)
            .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
            .with_for_update()
        )
        if auth_session is None:
            return
        if not hmac.compare_digest(
            auth_session.refresh_token_hash, hash_refresh_token(refresh_token)
        ):
            raise AppError("invalid_refresh_token", "Недействительный refresh token", status_code=401)
        if auth_session.revoked_at is None:
            auth_session.revoked_at = utcnow()
            await session.commit()
