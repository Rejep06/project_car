"""Схемы регистрации, входа и refresh/logout."""

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str = Field(min_length=20)


class LogoutRequest(RefreshRequest):
    """Тело запроса на отзыв refresh token."""


class TokenPairResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
