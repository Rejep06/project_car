"""Persist incoming support message receipts.

Revision ID: 0007_support_message_reads
Revises: 0006_legal_consent_evidence
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0007_support_message_reads"
down_revision: str | None = "0006_legal_consent_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "support_messages",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Establish a read baseline for existing history: only messages received
    # after deploying the new feature should light up the inbox.
    op.execute(sa.text("UPDATE support_messages SET read_at = CURRENT_TIMESTAMP"))
    op.create_index(
        "ix_support_messages_read_at_ticket_id",
        "support_messages",
        ["read_at", "ticket_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_support_messages_read_at_ticket_id", table_name="support_messages")
    with op.batch_alter_table("support_messages", schema=None) as batch_op:
        batch_op.drop_column("read_at")
