"""Импорт всех ORM-моделей для Alembic и настройки relationships."""

from app.db.models.audit import AuditLog
from app.db.models.auth_session import AuthSession
from app.db.models.deposit import (
    BlockchainDeposit,
    BlockchainSyncState,
    DepositAmountReservation,
    DepositInvoice,
    UnmatchedDeposit,
)
from app.db.models.deposit_wallet import DepositWallet
from app.db.models.email_auth import (
    EmailOutbox,
    EmailVerificationToken,
    LegalConsent,
    PasswordResetToken,
)
from app.db.models.lottery import (
    Lottery,
    LotteryPrize,
    LotteryTicket,
    LotteryTicketPurchase,
    LotteryWinner,
)
from app.db.models.notification import UserNotification
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
    "BlockchainDeposit",
    "BlockchainSyncState",
    "DepositAmountReservation",
    "DepositInvoice",
    "DepositWallet",
    "EmailOutbox",
    "EmailVerificationToken",
    "LegalConsent",
    "Lottery",
    "LotteryPrize",
    "LotteryTicket",
    "LotteryTicketPurchase",
    "LotteryWinner",
    "PasswordResetToken",
    "Post",
    "RewardPayout",
    "SubscriptionPlan",
    "SupportAttachment",
    "SupportMessage",
    "SupportTicket",
    "UnmatchedDeposit",
    "User",
    "UserNotification",
    "UserSubscription",
    "Wallet",
    "WalletTransaction",
    "WithdrawalRequest",
]
