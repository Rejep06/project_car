"""Добавляет признак позднего автоматического зачисления."""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_late_deposit_flag"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deposit_invoices",
        sa.Column("credited_after_expiration", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("deposit_invoices", "credited_after_expiration", server_default=None)


def downgrade() -> None:
    op.drop_column("deposit_invoices", "credited_after_expiration")
