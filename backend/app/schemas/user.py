"""Пользовательские и административные схемы профиля."""

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr

from app.db.enums import UserRole
from app.schemas.common import APIModel
from app.utils.money import format_amount


class UserRead(APIModel):
    id: UUID
    email: EmailStr
    pending_email: EmailStr | None
    email_verified_at: datetime | None
    email_verified: bool
    role: UserRole
    is_active: bool
    is_frozen: bool
    referral_code: str
    referred_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_user(cls, user: object) -> "UserRead":
        verified_at = getattr(user, "email_verified_at")
        return cls(
            id=getattr(user, "id"),
            email=getattr(user, "email"),
            pending_email=getattr(user, "pending_email"),
            email_verified_at=verified_at,
            email_verified=verified_at is not None,
            role=getattr(user, "role"),
            is_active=getattr(user, "is_active"),
            is_frozen=getattr(user, "is_frozen"),
            referral_code=getattr(user, "referral_code"),
            referred_by_user_id=getattr(user, "referred_by_user_id"),
            created_at=getattr(user, "created_at"),
            updated_at=getattr(user, "updated_at"),
        )


class UserUpdate(APIModel):
    email: EmailStr


class AdminUserRead(UserRead):
    available_balance: str
    locked_balance: str
    asset: str

    @classmethod
    def from_user(cls, user: object) -> "AdminUserRead":
        wallet = getattr(user, "wallet")
        base = UserRead.from_user(user)
        return cls(
            **base.model_dump(),
            available_balance=format_amount(wallet.available_balance_atomic),
            locked_balance=format_amount(wallet.locked_balance_atomic),
            asset=wallet.asset,
        )
