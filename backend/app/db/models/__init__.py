"""Импорт всех ORM-моделей для Alembic и настройки relationships."""

from app.db.models.audit import AuditLog
from app.db.models.auth_session import AuthSession
from app.db.models.deposit import (
    BinanceDeposit,
    DepositAmountReservation,
    DepositInvoice,
    UnmatchedDeposit,
)
from app.db.models.post import Post
from app.db.models.reward import RewardPayout
from app.db.models.subscription import SubscriptionPlan, UserSubscription
from app.db.models.support import SupportAttachment, SupportMessage, SupportTicket
from app.db.models.user import User
from app.db.models.wallet import Wallet, WalletTransaction
from app.db.models.withdrawal import WithdrawalRequest

__all__ = [
    "AuditLog",
    "AuthSession",
    "BinanceDeposit",
    "DepositAmountReservation",
    "DepositInvoice",
    "Post",
    "RewardPayout",
    "SubscriptionPlan",
    "SupportAttachment",
    "SupportMessage",
    "SupportTicket",
    "UnmatchedDeposit",
    "User",
    "UserSubscription",
    "Wallet",
    "WalletTransaction",
    "WithdrawalRequest",
]
