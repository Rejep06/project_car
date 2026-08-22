"""Добавляет подтверждение email, восстановление пароля и лотереи.

Revision ID: 0005_email_lottery
Revises: 0004_infura_erc20
Create Date: 2026-08-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_email_lottery"
down_revision: str | None = "0004_infura_erc20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


wallet_operation_type_enum = sa.Enum(
    "deposit_credit",
    "program_purchase",
    "reward_credit",
    "referral_purchase_bonus",
    "referral_reward_bonus",
    "lottery_ticket_purchase",
    "lottery_prize_credit",
    "lottery_ticket_refund",
    "withdrawal_hold",
    "withdrawal_complete",
    "withdrawal_refund",
    "admin_adjustment",
    name="wallet_operation_type",
    native_enum=False,
)

email_verification_purpose_enum = sa.Enum(
    "registration",
    "email_change",
    name="email_verification_purpose",
    native_enum=False,
)
email_outbox_status_enum = sa.Enum(
    "pending",
    "sending",
    "sent",
    "failed",
    name="email_outbox_status",
    native_enum=False,
)
legal_document_type_enum = sa.Enum(
    "terms_of_use",
    "privacy_policy",
    "personal_data_processing",
    "program_rules",
    "age_confirmation",
    name="legal_document_type",
    native_enum=False,
)
notification_type_enum = sa.Enum(
    "lottery_win",
    "system",
    name="notification_type",
    native_enum=False,
)
lottery_status_enum = sa.Enum(
    "draft",
    "published",
    "awaiting_confirmation",
    "completed",
    "cancelled",
    name="lottery_status",
    native_enum=False,
)
lottery_prize_type_enum = sa.Enum(
    "balance",
    "physical",
    name="lottery_prize_type",
    native_enum=False,
)
lottery_ticket_status_enum = sa.Enum(
    "active",
    "refunded",
    name="lottery_ticket_status",
    native_enum=False,
)
lottery_winner_selection_method_enum = sa.Enum(
    "random",
    "manual",
    name="lottery_winner_selection_method",
    native_enum=False,
)
lottery_winner_status_enum = sa.Enum(
    "pending",
    "confirmed",
    "cancelled",
    name="lottery_winner_status",
    native_enum=False,
)


def upgrade() -> None:
    # Существующие аккаунты считаются подтверждёнными, чтобы обновление не
    # заблокировало текущих пользователей и администратора.
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pending_email", sa.String(length=320), nullable=True))
        batch_op.add_column(
            sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            batch_op.f("ix_users_pending_email"), ["pending_email"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_users_email_verified_at"),
            ["email_verified_at"],
            unique=False,
        )

    op.execute(
        sa.text(
            "UPDATE users SET email_verified_at = created_at "
            "WHERE email_verified_at IS NULL"
        )
    )

    with op.batch_alter_table("wallet_transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "operation_type",
            existing_type=sa.String(length=23),
            type_=wallet_operation_type_enum,
            existing_nullable=False,
        )

    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("purpose", email_verification_purpose_enum, nullable=False),
        sa.Column("target_email", sa.String(length=320), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_email_verification_tokens_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_verification_tokens")),
    )
    op.create_index(
        op.f("ix_email_verification_tokens_user_id"),
        "email_verification_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_verification_tokens_token_hash"),
        "email_verification_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_email_verification_tokens_expires_at"),
        "email_verification_tokens",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_password_reset_tokens_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_reset_tokens")),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"),
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_token_hash"),
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_password_reset_tokens_expires_at"),
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )

    op.create_table(
        "legal_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", legal_document_type_enum, nullable=False),
        sa.Column("document_version", sa.String(length=40), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_legal_consents_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_legal_consents")),
        sa.UniqueConstraint(
            "user_id",
            "document_type",
            "document_version",
            name="uq_legal_consent_user_document_version",
        ),
    )
    op.create_index(
        op.f("ix_legal_consents_user_id"),
        "legal_consents",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "email_outbox",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("status", email_outbox_status_enum, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_email_outbox")),
    )
    op.create_index(
        op.f("ix_email_outbox_recipient_email"),
        "email_outbox",
        ["recipient_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_email_outbox_status"), "email_outbox", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_email_outbox_available_at"),
        "email_outbox",
        ["available_at"],
        unique=False,
    )

    op.create_table(
        "user_notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("notification_type", notification_type_enum, nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(length=1000), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE", name=op.f("fk_user_notifications_user_id_users")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_notifications")),
    )
    op.create_index(
        op.f("ix_user_notifications_user_id"),
        "user_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_is_read"),
        "user_notifications",
        ["is_read"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_notifications_created_at"),
        "user_notifications",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "lotteries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=1000), nullable=True),
        sa.Column("status", lottery_status_enum, nullable=False),
        sa.Column("ticket_price_atomic", sa.BigInteger(), nullable=False),
        sa.Column("sales_start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sales_end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("draw_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_tickets_total", sa.Integer(), nullable=True),
        sa.Column("max_tickets_per_user", sa.Integer(), nullable=False),
        sa.Column("manager_telegram", sa.String(length=120), nullable=True),
        sa.Column("rules_text", sa.Text(), nullable=False),
        sa.Column("rules_version", sa.String(length=40), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "ticket_price_atomic > 0", name=op.f("ck_lotteries_ticket_price_positive")
        ),
        sa.CheckConstraint(
            "max_tickets_total IS NULL OR max_tickets_total > 0",
            name=op.f("ck_lotteries_max_tickets_total_positive"),
        ),
        sa.CheckConstraint(
            "max_tickets_per_user > 0",
            name=op.f("ck_lotteries_max_tickets_per_user_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lotteries_created_by_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lotteries")),
    )
    for column in ("status", "sales_start_at", "sales_end_at", "draw_at"):
        op.create_index(op.f(f"ix_lotteries_{column}"), "lotteries", [column], unique=False)

    op.create_table(
        "lottery_prizes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lottery_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("prize_type", lottery_prize_type_enum, nullable=False),
        sa.Column("amount_atomic", sa.BigInteger(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("manager_telegram", sa.String(length=120), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_lottery_prizes_quantity_positive")),
        sa.CheckConstraint(
            "amount_atomic IS NULL OR amount_atomic > 0",
            name=op.f("ck_lottery_prizes_amount_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["lottery_id"],
            ["lotteries.id"],
            ondelete="CASCADE",
            name=op.f("fk_lottery_prizes_lottery_id_lotteries"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lottery_prizes")),
    )
    op.create_index(
        op.f("ix_lottery_prizes_lottery_id"),
        "lottery_prizes",
        ["lottery_id"],
        unique=False,
    )

    op.create_table(
        "lottery_ticket_purchases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lottery_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("total_amount_atomic", sa.BigInteger(), nullable=False),
        sa.Column("wallet_transaction_id", sa.Uuid(), nullable=False),
        sa.Column("rules_version", sa.String(length=40), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lottery_id"],
            ["lotteries.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_ticket_purchases_lottery_id_lotteries"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_ticket_purchases_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["wallet_transaction_id"],
            ["wallet_transactions.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_ticket_purchases_wallet_transaction_id_wallet_transactions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lottery_ticket_purchases")),
        sa.UniqueConstraint(
            "wallet_transaction_id",
            name=op.f("uq_lottery_ticket_purchases_wallet_transaction_id"),
        ),
    )
    op.create_index(
        op.f("ix_lottery_ticket_purchases_lottery_id"),
        "lottery_ticket_purchases",
        ["lottery_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_lottery_ticket_purchases_user_id"),
        "lottery_ticket_purchases",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "lottery_tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("lottery_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_code", sa.String(length=32), nullable=False),
        sa.Column("price_atomic", sa.BigInteger(), nullable=False),
        sa.Column("status", lottery_ticket_status_enum, nullable=False),
        sa.Column(
            "purchased_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["purchase_id"],
            ["lottery_ticket_purchases.id"],
            ondelete="CASCADE",
            name=op.f("fk_lottery_tickets_purchase_id_lottery_ticket_purchases"),
        ),
        sa.ForeignKeyConstraint(
            ["lottery_id"],
            ["lotteries.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_tickets_lottery_id_lotteries"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_tickets_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lottery_tickets")),
        sa.UniqueConstraint(
            "lottery_id", "ticket_code", name="uq_lottery_ticket_code"
        ),
    )
    for column in ("purchase_id", "lottery_id", "user_id", "ticket_code", "status", "purchased_at"):
        op.create_index(
            op.f(f"ix_lottery_tickets_{column}"),
            "lottery_tickets",
            [column],
            unique=False,
        )

    op.create_table(
        "lottery_winners",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lottery_id", sa.Uuid(), nullable=False),
        sa.Column("prize_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("selection_method", lottery_winner_selection_method_enum, nullable=False),
        sa.Column("status", lottery_winner_status_enum, nullable=False),
        sa.Column("selected_by_user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "selected_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("confirmed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("wallet_transaction_id", sa.Uuid(), nullable=True),
        sa.Column("claim_contact", sa.String(length=300), nullable=True),
        sa.Column("confirmation_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["lottery_id"],
            ["lotteries.id"],
            ondelete="CASCADE",
            name=op.f("fk_lottery_winners_lottery_id_lotteries"),
        ),
        sa.ForeignKeyConstraint(
            ["prize_id"],
            ["lottery_prizes.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_prize_id_lottery_prizes"),
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["lottery_tickets.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_ticket_id_lottery_tickets"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["selected_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_selected_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["confirmed_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_confirmed_by_user_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["wallet_transaction_id"],
            ["wallet_transactions.id"],
            ondelete="RESTRICT",
            name=op.f("fk_lottery_winners_wallet_transaction_id_wallet_transactions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lottery_winners")),
        sa.UniqueConstraint("ticket_id", name="uq_lottery_winner_ticket"),
    )
    for column in ("lottery_id", "prize_id", "user_id", "status"):
        op.create_index(
            op.f(f"ix_lottery_winners_{column}"),
            "lottery_winners",
            [column],
            unique=False,
        )


def downgrade() -> None:
    op.drop_table("lottery_winners")
    op.drop_table("lottery_tickets")
    op.drop_table("lottery_ticket_purchases")
    op.drop_table("lottery_prizes")
    op.drop_table("lotteries")
    op.drop_table("user_notifications")
    op.drop_table("email_outbox")
    op.drop_table("legal_consents")
    op.drop_table("password_reset_tokens")
    op.drop_table("email_verification_tokens")

    old_wallet_operation_type = sa.Enum(
        "deposit_credit",
        "program_purchase",
        "reward_credit",
        "referral_purchase_bonus",
        "referral_reward_bonus",
        "withdrawal_hold",
        "withdrawal_complete",
        "withdrawal_refund",
        "admin_adjustment",
        name="wallet_operation_type",
        native_enum=False,
    )
    with op.batch_alter_table("wallet_transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "operation_type",
            existing_type=wallet_operation_type_enum,
            type_=old_wallet_operation_type,
            existing_nullable=False,
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email_verified_at"))
        batch_op.drop_index(batch_op.f("ix_users_pending_email"))
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("pending_email")
