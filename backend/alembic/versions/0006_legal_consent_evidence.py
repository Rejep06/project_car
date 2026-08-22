"""Расширяет доказательную запись электронных согласий.

Revision ID: 0006_legal_consent_evidence
Revises: 0005_email_lottery
Create Date: 2026-08-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0006_legal_consent_evidence"
down_revision: str | None = "0005_email_lottery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Поля nullable намеренно: старые записи нельзя дополнять вымышленной
    # формулировкой акцепта. Все новые регистрации заполняют их полностью.
    with op.batch_alter_table("legal_consents", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("acceptance_batch_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("acceptance_form_version", sa.String(length=40), nullable=True)
        )
        batch_op.add_column(
            sa.Column("consent_group", sa.String(length=40), nullable=True)
        )
        batch_op.add_column(
            sa.Column("account_email", sa.String(length=320), nullable=True)
        )
        batch_op.add_column(
            sa.Column("document_url", sa.String(length=500), nullable=True)
        )
        batch_op.add_column(sa.Column("acceptance_text", sa.Text(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_legal_consents_acceptance_batch_id"),
            ["acceptance_batch_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("legal_consents", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_legal_consents_acceptance_batch_id"))
        batch_op.drop_column("acceptance_text")
        batch_op.drop_column("document_url")
        batch_op.drop_column("account_email")
        batch_op.drop_column("consent_group")
        batch_op.drop_column("acceptance_form_version")
        batch_op.drop_column("acceptance_batch_id")
