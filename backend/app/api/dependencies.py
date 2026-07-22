"""Зависимости FastAPI для авторизации, ролей и заголовков."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import TokenValidationError, decode_token
from app.db.enums import UserRole
from app.db.models import User
from app.db.session import get_session

bearer_scheme = HTTPBearer(auto_error=False)
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    """Проверяет access token и загружает только активного пользователя."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("authentication_required", "Требуется авторизация", status_code=401)
    try:
        payload = decode_token(credentials.credentials, "access")
        user_id = UUID(payload["sub"])
    except (TokenValidationError, KeyError, ValueError) as exc:
        raise AppError("invalid_access_token", "Недействительный access token", status_code=401) from exc
    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise AppError("user_inactive", "Пользователь недоступен", status_code=403)
    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Разрешает доступ только роли admin."""
    if current_user.role != UserRole.ADMIN:
        raise AppError("admin_required", "Требуются права администратора", status_code=403)
    return current_user


async def get_idempotency_key(
    idempotency_key: Annotated[
        str,
        Header(alias="Idempotency-Key", min_length=1, max_length=255),
    ],
) -> str:
    """Нормализует обязательный Idempotency-Key."""
    normalized = idempotency_key.strip()
    if not normalized:
        raise AppError("invalid_idempotency_key", "Idempotency-Key не может быть пустым")
    return normalized

CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentAdminDep = Annotated[User, Depends(get_current_admin)]
IdempotencyKeyDep = Annotated[str, Depends(get_idempotency_key)]
