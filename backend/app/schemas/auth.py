"""Схемы регистрации, подтверждения email, входа и восстановления пароля."""

from typing import Literal

from pydantic import EmailStr, Field, field_validator

from app.schemas.common import APIModel


class RegisterRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    referral_code: str | None = Field(default=None, min_length=4, max_length=20)
    # Frontend показывает три чекбокса, но передаёт пять отдельных признаков,
    # чтобы backend мог сохранить согласие с каждой версией документа.
    accept_terms: Literal[True] = Field(
        description="Принятие Пользовательского соглашения"
    )
    accept_privacy_policy: Literal[True] = Field(
        description="Ознакомление с Политикой конфиденциальности"
    )
    accept_personal_data_processing: Literal[True] = Field(
        description="Согласие на обработку персональных данных"
    )
    accept_program_rules: Literal[True] = Field(
        description="Принятие правил клиентских программ и лотерей"
    )
    confirm_age_18: Literal[True] = Field(
        description="Подтверждение совершеннолетия и дееспособности"
    )

    @field_validator("referral_code")
    @classmethod
    def normalize_referral_code(cls, value: str | None) -> str | None:
        normalized = value.strip().upper() if value else None
        return normalized or None


class RegistrationResponse(APIModel):
    email: EmailStr
    verification_required: bool = True
    message: str
    debug_verification_token: str | None = None


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


class EmailVerificationConfirmRequest(APIModel):
    token: str = Field(min_length=32, max_length=512)


class EmailVerificationResendRequest(APIModel):
    email: EmailStr


class EmailVerificationResponse(APIModel):
    message: str
    email: EmailStr | None = None


class PasswordResetRequest(APIModel):
    email: EmailStr


class PasswordResetConfirmRequest(APIModel):
    token: str = Field(min_length=32, max_length=512)
    new_password: str = Field(min_length=8, max_length=128)
