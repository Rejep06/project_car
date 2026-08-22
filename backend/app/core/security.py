"""Пароли, JWT и хеширование refresh token."""

import hashlib
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.utils.datetime import utcnow

_password_hash = PasswordHash.recommended()


class TokenValidationError(ValueError):
    """JWT отсутствует, повреждён, истёк или имеет неверный тип."""


def hash_password(password: str) -> str:
    """Хеширует пароль Argon2 через pwdlib."""
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Проверяет пароль без раскрытия причины несовпадения."""
    return _password_hash.verify(password, password_hash)


def hash_refresh_token(token: str) -> str:
    """Создаёт необратимый SHA-256 хеш refresh token для хранения в БД."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_action_token(token: str) -> str:
    """Хеширует одноразовый токен подтверждения email или сброса пароля."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, role: str) -> tuple[str, int]:
    """Создаёт короткоживущий access token и возвращает TTL в секундах."""
    settings = get_settings()
    ttl = timedelta(minutes=settings.access_token_expire_minutes)
    now = utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + ttl,
    }
    return (
        jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm),
        int(ttl.total_seconds()),
    )


def create_refresh_token(user_id: UUID, session_id: UUID) -> str:
    """Создаёт refresh token, связанный с серверной auth-сессией."""
    settings = get_settings()
    now = utcnow()
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "type": "refresh",
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + timedelta(days=settings.refresh_token_expire_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Проверяет подпись JWT и ожидаемый тип токена."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except InvalidTokenError as exc:
        raise TokenValidationError("Недействительный токен") from exc
    if payload.get("type") != expected_type:
        raise TokenValidationError("Неверный тип токена")
    return payload
