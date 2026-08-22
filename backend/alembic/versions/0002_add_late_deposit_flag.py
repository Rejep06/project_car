"""Добавляет признак позднего автоматического зачисления."""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_late_deposit_flag"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch-режим сохраняет ту же миграцию совместимой и с PostgreSQL, и с SQLite.
    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "credited_after_expiration",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.alter_column(
            "credited_after_expiration",
            existing_type=sa.Boolean(),
            server_default=None,
        )


def downgrade() -> None:
    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.drop_column("credited_after_expiration")
