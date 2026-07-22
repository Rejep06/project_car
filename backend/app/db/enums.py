"""Перечисления доменной модели, хранимые в БД строковыми значениями."""

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class WalletOperationType(StrEnum):
    DEPOSIT_CREDIT = "deposit_credit"
    SUBSCRIPTION_PURCHASE = "subscription_purchase"
    REWARD_CREDIT = "reward_credit"
    WITHDRAWAL_HOLD = "withdrawal_hold"
    WITHDRAWAL_COMPLETE = "withdrawal_complete"
    WITHDRAWAL_REFUND = "withdrawal_refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class PlanCategory(StrEnum):
    GAME = "game"
    APPLICATION = "application"


class DurationUnit(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class RewardFrequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class UserSubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RewardPayoutStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DepositInvoiceStatus(StrEnum):
    WAITING = "waiting"
    DETECTED = "detected"
    CREDITED = "credited"
    EXPIRED = "expired"
    MANUAL_REVIEW = "manual_review"
    CANCELLED = "cancelled"


class BinanceDepositStatus(StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    REJECTED = "rejected"
    CREDITED_LOCKED = "credited_locked"
    WRONG_DEPOSIT = "wrong_deposit"
    WAITING_CONFIRMATION = "waiting_confirmation"
    UNKNOWN = "unknown"


class UnmatchedDepositStatus(StrEnum):
    UNRESOLVED = "unresolved"
    ASSIGNED = "assigned"
    IGNORED = "ignored"


class UnmatchedDepositReason(StrEnum):
    WRONG_AMOUNT = "wrong_amount"
    EXPIRED_INVOICE = "expired_invoice"
    INVOICE_NOT_FOUND = "invoice_not_found"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    UNKNOWN = "unknown"


class SupportTicketCategory(StrEnum):
    DEPOSIT_PROBLEM = "deposit_problem"
    WITHDRAWAL_PROBLEM = "withdrawal_problem"
    SUBSCRIPTION_PROBLEM = "subscription_problem"
    OTHER = "other"


class SupportTicketStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    WAITING_USER = "waiting_user"
    RESOLVED = "resolved"
    CLOSED = "closed"


class WithdrawalStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SENT = "sent"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PostStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
