"""Persist deposit request idempotency without rewriting existing records.

Revision ID: 0008_mobile_deposit_idempotency
Revises: 0007_support_message_reads
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0008_mobile_deposit_idempotency"
down_revision: str | None = "0007_support_message_reads"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("deposit_invoices") as batch_op:
        batch_op.add_column(sa.Column("request_idempotency_key", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("request_fingerprint", sa.String(64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_deposit_invoices_request_idempotency_key", ["request_idempotency_key"]
        )


def downgrade() -> None:
    with op.batch_alter_table("deposit_invoices") as batch_op:
        batch_op.drop_constraint("uq_deposit_invoices_request_idempotency_key", type_="unique")
        batch_op.drop_column("request_fingerprint")
        batch_op.drop_column("request_idempotency_key")
