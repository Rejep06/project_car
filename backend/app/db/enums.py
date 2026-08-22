"""Перечисления доменной модели, хранимые в БД строковыми значениями."""

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class WalletOperationType(StrEnum):
    DEPOSIT_CREDIT = "deposit_credit"
    PROGRAM_PURCHASE = "program_purchase"
    REWARD_CREDIT = "reward_credit"
    REFERRAL_PURCHASE_BONUS = "referral_purchase_bonus"
    REFERRAL_REWARD_BONUS = "referral_reward_bonus"
    LOTTERY_TICKET_PURCHASE = "lottery_ticket_purchase"
    LOTTERY_PRIZE_CREDIT = "lottery_prize_credit"
    LOTTERY_TICKET_REFUND = "lottery_ticket_refund"
    WITHDRAWAL_HOLD = "withdrawal_hold"
    WITHDRAWAL_COMPLETE = "withdrawal_complete"
    WITHDRAWAL_REFUND = "withdrawal_refund"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class PlanTier(StrEnum):
    STARTER = "starter"
    STANDARD = "standard"
    PREMIUM = "premium"


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


class BlockchainDepositStatus(StrEnum):
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


class EmailVerificationPurpose(StrEnum):
    REGISTRATION = "registration"
    EMAIL_CHANGE = "email_change"


class EmailOutboxStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class LegalDocumentType(StrEnum):
    TERMS_OF_USE = "terms_of_use"
    PRIVACY_POLICY = "privacy_policy"
    PERSONAL_DATA_PROCESSING = "personal_data_processing"
    PROGRAM_RULES = "program_rules"
    AGE_CONFIRMATION = "age_confirmation"


class LotteryStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LotteryPrizeType(StrEnum):
    BALANCE = "balance"
    PHYSICAL = "physical"


class LotteryTicketStatus(StrEnum):
    ACTIVE = "active"
    REFUNDED = "refunded"


class LotteryWinnerSelectionMethod(StrEnum):
    RANDOM = "random"
    MANUAL = "manual"


class LotteryWinnerStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class NotificationType(StrEnum):
    LOTTERY_WIN = "lottery_win"
    SYSTEM = "system"
