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
    role: UserRole
    is_active: bool
    is_frozen: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(APIModel):
    email: EmailStr


class AdminUserRead(UserRead):
    available_balance: str
    locked_balance: str
    asset: str

    @classmethod
    def from_user(cls, user: object) -> "AdminUserRead":
        wallet = getattr(user, "wallet")
        return cls(
            id=getattr(user, "id"),
            email=getattr(user, "email"),
            role=getattr(user, "role"),
            is_active=getattr(user, "is_active"),
            is_frozen=getattr(user, "is_frozen"),
            created_at=getattr(user, "created_at"),
            updated_at=getattr(user, "updated_at"),
            available_balance=format_amount(wallet.available_balance_atomic),
            locked_balance=format_amount(wallet.locked_balance_atomic),
            asset=wallet.asset,
        )
