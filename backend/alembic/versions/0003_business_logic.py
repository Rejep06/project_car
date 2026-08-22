"""Добавляет уровни программ, рефералов и несколько кошельков пополнения.

Revision ID: 0003_business_logic
Revises: 0002_add_late_deposit_flag
Create Date: 2026-08-01
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_business_logic"
down_revision: str | None = "0002_add_late_deposit_flag"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


plan_tier_enum = sa.Enum(
    "starter",
    "standard",
    "premium",
    name="plan_tier",
    native_enum=False,
)
purchased_plan_tier_enum = sa.Enum(
    "starter",
    "standard",
    "premium",
    name="purchased_plan_tier",
    native_enum=False,
)
plan_category_enum = sa.Enum(
    "game",
    "application",
    name="plan_category",
    native_enum=False,
)


def _backfill_referral_codes() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM users")).mappings().all()
    used: set[str] = set()
    for number, row in enumerate(rows, start=1):
        compact = str(row["id"]).replace("-", "").upper()
        code = compact[:16] or f"USER{number:012d}"
        suffix = 1
        candidate = code
        while candidate in used:
            tail = f"{suffix:X}"
            candidate = f"{code[: 20 - len(tail)]}{tail}"
            suffix += 1
        used.add(candidate)
        connection.execute(
            sa.text("UPDATE users SET referral_code = :code WHERE id = :user_id"),
            {"code": candidate, "user_id": row["id"]},
        )


def upgrade() -> None:
    op.create_table(
        "deposit_wallets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("asset", sa.String(length=16), nullable=False),
        sa.Column("network", sa.String(length=32), nullable=False),
        sa.Column("network_display_name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deposit_wallets")),
        sa.UniqueConstraint(
            "network",
            "address",
            name="uq_deposit_wallet_network_address",
        ),
    )
    with op.batch_alter_table("deposit_wallets", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_deposit_wallets_is_active"),
            ["is_active"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_deposit_wallets_sort_order"),
            ["sort_order"],
            unique=False,
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("referral_code", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("referred_by_user_id", sa.Uuid(), nullable=True))

    _backfill_referral_codes()

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "referral_code",
            existing_type=sa.String(length=20),
            nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix_users_referral_code"),
            ["referral_code"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_users_referred_by_user_id"),
            ["referred_by_user_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_users_referred_by_user_id_users"),
            "users",
            ["referred_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    with op.batch_alter_table("subscription_plans", schema=None) as batch_op:
        batch_op.add_column(sa.Column("tier", plan_tier_enum, nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE subscription_plans
            SET tier = CASE
                WHEN category = 'game' THEN 'starter'
                WHEN category = 'application' THEN 'standard'
                ELSE 'standard'
            END
            """
        )
    )

    with op.batch_alter_table("user_subscriptions", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("plan_tier", purchased_plan_tier_enum, nullable=True)
        )

    op.execute(
        sa.text(
            """
            UPDATE user_subscriptions
            SET plan_tier = (
                SELECT subscription_plans.tier
                FROM subscription_plans
                WHERE subscription_plans.id = user_subscriptions.plan_id
            )
            """
        )
    )

    with op.batch_alter_table("user_subscriptions", schema=None) as batch_op:
        batch_op.alter_column(
            "plan_tier",
            existing_type=purchased_plan_tier_enum,
            nullable=False,
        )

    with op.batch_alter_table("subscription_plans", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_subscription_plans_slug"))
        batch_op.alter_column(
            "tier",
            existing_type=plan_tier_enum,
            nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix_subscription_plans_tier"),
            ["tier"],
            unique=False,
        )
        batch_op.drop_column("category")
        batch_op.drop_column("slug")

    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.add_column(sa.Column("deposit_wallet_id", sa.Uuid(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_deposit_invoices_deposit_wallet_id"),
            ["deposit_wallet_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_deposit_invoices_deposit_wallet_id_deposit_wallets"),
            "deposit_wallets",
            ["deposit_wallet_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        sa.text(
            """
            UPDATE wallet_transactions
            SET operation_type = 'program_purchase'
            WHERE operation_type = 'subscription_purchase'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE wallet_transactions
            SET operation_type = CASE
                WHEN operation_type = 'program_purchase' THEN 'subscription_purchase'
                WHEN operation_type IN ('referral_purchase_bonus', 'referral_reward_bonus')
                    THEN 'admin_adjustment'
                ELSE operation_type
            END
            """
        )
    )

    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_deposit_invoices_deposit_wallet_id_deposit_wallets"),
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_deposit_invoices_deposit_wallet_id"))
        batch_op.drop_column("deposit_wallet_id")

    with op.batch_alter_table("subscription_plans", schema=None) as batch_op:
        batch_op.add_column(sa.Column("slug", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("category", plan_category_enum, nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, tier FROM subscription_plans")
    ).mappings().all()
    for row in rows:
        compact = str(row["id"]).replace("-", "").lower()
        category = "game" if row["tier"] == "starter" else "application"
        connection.execute(
            sa.text(
                """
                UPDATE subscription_plans
                SET slug = :slug, category = :category
                WHERE id = :plan_id
                """
            ),
            {
                "slug": f"program-{compact}",
                "category": category,
                "plan_id": row["id"],
            },
        )

    with op.batch_alter_table("subscription_plans", schema=None) as batch_op:
        batch_op.alter_column(
            "slug",
            existing_type=sa.String(length=200),
            nullable=False,
        )
        batch_op.alter_column(
            "category",
            existing_type=plan_category_enum,
            nullable=False,
        )
        batch_op.create_index(
            batch_op.f("ix_subscription_plans_slug"),
            ["slug"],
            unique=True,
        )
        batch_op.drop_index(batch_op.f("ix_subscription_plans_tier"))
        batch_op.drop_column("tier")

    with op.batch_alter_table("user_subscriptions", schema=None) as batch_op:
        batch_op.drop_column("plan_tier")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_users_referred_by_user_id_users"),
            type_="foreignkey",
        )
        batch_op.drop_index(batch_op.f("ix_users_referred_by_user_id"))
        batch_op.drop_index(batch_op.f("ix_users_referral_code"))
        batch_op.drop_column("referred_by_user_id")
        batch_op.drop_column("referral_code")

    with op.batch_alter_table("deposit_wallets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_deposit_wallets_sort_order"))
        batch_op.drop_index(batch_op.f("ix_deposit_wallets_is_active"))
    op.drop_table("deposit_wallets")
