"""Пользователь, его роль, подтверждение email и реферальная связь."""

from __future__ import annotations

from datetime import datetime
import secrets
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.base import Base, TimestampMixin
from app.db.enums import UserRole


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    pending_email: Mapped[str | None] = mapped_column(
        String(320), unique=True, index=True, nullable=True
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    referral_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: secrets.token_hex(8).upper(),
    )
    referred_by_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    wallet = relationship("Wallet", back_populates="user", uselist=False, lazy="selectin")
    auth_sessions = relationship("AuthSession", back_populates="user", lazy="raise")
    referrer = relationship(
        "User",
        remote_side=[id],
        foreign_keys=[referred_by_user_id],
        back_populates="referrals",
        lazy="selectin",
    )
    referrals = relationship(
        "User",
        foreign_keys=[referred_by_user_id],
        back_populates="referrer",
        lazy="raise",
    )
    notifications = relationship("UserNotification", back_populates="user", lazy="raise")

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None
