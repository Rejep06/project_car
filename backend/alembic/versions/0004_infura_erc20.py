"""Переводит проверку пополнений на универсальные блокчейн-события и Infura.

Revision ID: 0004_infura_erc20
Revises: 0003_business_logic
Create Date: 2026-08-03
"""

from collections.abc import Sequence
import re

from alembic import op
import sqlalchemy as sa


revision: str = "0004_infura_erc20"
down_revision: str | None = "0003_business_logic"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

USDT_ETHEREUM_CONTRACT = "0xdac17f958d2ee523a2206206994597c13d831ec7"

wallet_operation_type_enum = sa.Enum(
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


def upgrade() -> None:
    # Кошелёк теперь хранит собственную конфигурацию сети и провайдера.
    with op.batch_alter_table("deposit_wallets", schema=None) as batch_op:
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column("provider", sa.String(length=40), server_default="manual", nullable=False)
        )
        batch_op.add_column(sa.Column("provider_network", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("chain_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("token_standard", sa.String(length=32), nullable=True))
        batch_op.add_column(
            sa.Column("token_contract_address", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(
            sa.Column("token_decimals", sa.Integer(), server_default="6", nullable=False)
        )
        batch_op.add_column(
            sa.Column("confirmations_required", sa.Integer(), server_default="12", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "monitoring_enabled", sa.Boolean(), server_default=sa.false(), nullable=False
            )
        )
        batch_op.create_index(
            batch_op.f("ix_deposit_wallets_monitoring_enabled"),
            ["monitoring_enabled"],
            unique=False,
        )

    # Старые адреса других провайдеров не публикуются автоматически. Только
    # корректные EVM-адреса можно безопасно перевести на Ethereum/Infura.
    wallet_table = sa.table(
        "deposit_wallets",
        sa.column("id"),
        sa.column("address"),
        sa.column("provider"),
        sa.column("provider_network"),
        sa.column("chain_id"),
        sa.column("token_standard"),
        sa.column("token_contract_address"),
        sa.column("token_decimals"),
        sa.column("confirmations_required"),
        sa.column("monitoring_enabled"),
        sa.column("network"),
        sa.column("network_display_name"),
        sa.column("is_active"),
    )
    bind = op.get_bind()
    evm_address_pattern = re.compile(r"^0x[0-9a-fA-F]{40}$")
    old_wallets = bind.execute(
        sa.select(wallet_table.c.id, wallet_table.c.address)
    ).all()
    for wallet_id, address in old_wallets:
        normalized_address = str(address or "").strip().lower()
        if evm_address_pattern.fullmatch(normalized_address):
            bind.execute(
                wallet_table.update()
                .where(wallet_table.c.id == wallet_id)
                .values(
                    address=normalized_address,
                    provider="infura",
                    provider_network="mainnet",
                    chain_id=1,
                    token_standard="ERC20",
                    token_contract_address=USDT_ETHEREUM_CONTRACT,
                    token_decimals=6,
                    confirmations_required=12,
                    monitoring_enabled=True,
                    network="ETHEREUM",
                    network_display_name="Ethereum (ERC-20)",
                )
            )
        else:
            bind.execute(
                wallet_table.update()
                .where(wallet_table.c.id == wallet_id)
                .values(is_active=False, monitoring_enabled=False)
            )

    # Нормализованная запись больше не зависит от конкретной биржи.
    op.rename_table("binance_deposits", "blockchain_deposits")
    with op.batch_alter_table("blockchain_deposits", schema=None) as batch_op:
        batch_op.drop_index("ix_binance_deposits_binance_deposit_id")
        batch_op.drop_index("ix_binance_deposits_detected_at")
        batch_op.drop_index("ix_binance_deposits_txid")
        batch_op.drop_constraint(
            "uq_binance_deposits_deposit_invoice_id", type_="unique"
        )
        batch_op.alter_column(
            "binance_deposit_id",
            new_column_name="external_id",
            existing_type=sa.String(length=255),
            nullable=False,
        )
        batch_op.alter_column(
            "coin",
            new_column_name="asset",
            existing_type=sa.String(length=32),
            nullable=False,
        )
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        batch_op.add_column(
            sa.Column("log_index", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(sa.Column("block_number", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("block_hash", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("from_address", sa.String(length=256), nullable=True))
        batch_op.add_column(
            sa.Column("provider", sa.String(length=40), server_default="legacy", nullable=False)
        )
        batch_op.add_column(
            sa.Column("token_contract_address", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(
            sa.Column("confirmations", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.drop_constraint("uq_binance_deposit_network_txid", type_="unique")

    with op.batch_alter_table("blockchain_deposits", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_blockchain_deposit_network_txid_log",
            ["network", "txid", "log_index"],
        )
        batch_op.create_unique_constraint(
            batch_op.f("uq_blockchain_deposits_deposit_invoice_id"),
            ["deposit_invoice_id"],
        )
        batch_op.create_index(
            batch_op.f("ix_blockchain_deposits_external_id"),
            ["external_id"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_blockchain_deposits_detected_at"),
            ["detected_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_blockchain_deposits_txid"),
            ["txid"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_blockchain_deposits_block_number"),
            ["block_number"],
            unique=False,
        )

    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "matched_binance_deposit_id",
            new_column_name="matched_blockchain_deposit_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )

    with op.batch_alter_table("unmatched_deposits", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_unmatched_deposits_binance_deposit_id", type_="unique"
        )
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "binance_deposit_id",
            new_column_name="blockchain_deposit_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )

    with op.batch_alter_table("unmatched_deposits", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            batch_op.f("uq_unmatched_deposits_blockchain_deposit_id"),
            ["blockchain_deposit_id"],
        )

    # В 0003 появились реферальные операции, одна из которых длиннее старого
    # VARCHAR(21). Расширяем колонку, иначе PostgreSQL отклоняет начисление.
    with op.batch_alter_table("wallet_transactions", schema=None) as batch_op:
        batch_op.alter_column(
            "operation_type",
            existing_type=sa.String(length=21),
            type_=wallet_operation_type_enum,
            existing_nullable=False,
        )

    with op.batch_alter_table("support_tickets", schema=None) as batch_op:
        batch_op.alter_column(
            "related_binance_deposit_id",
            new_column_name="related_blockchain_deposit_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )

    op.create_table(
        "blockchain_sync_states",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sync_key", sa.String(length=500), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_network", sa.String(length=80), nullable=False),
        sa.Column("chain_id", sa.Integer(), nullable=False),
        sa.Column("network", sa.String(length=64), nullable=False),
        sa.Column("token_contract_address", sa.String(length=256), nullable=False),
        sa.Column("last_scanned_block", sa.BigInteger(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blockchain_sync_states")),
    )
    with op.batch_alter_table("blockchain_sync_states", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_blockchain_sync_states_sync_key"), ["sync_key"], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table("blockchain_sync_states", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_blockchain_sync_states_sync_key"))
    op.drop_table("blockchain_sync_states")

    with op.batch_alter_table("support_tickets", schema=None) as batch_op:
        batch_op.alter_column(
            "related_blockchain_deposit_id",
            new_column_name="related_binance_deposit_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )

    with op.batch_alter_table("unmatched_deposits", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("uq_unmatched_deposits_blockchain_deposit_id"),
            type_="unique",
        )
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "blockchain_deposit_id",
            new_column_name="binance_deposit_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )

    with op.batch_alter_table("unmatched_deposits", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_unmatched_deposits_binance_deposit_id", ["binance_deposit_id"]
        )

    with op.batch_alter_table("deposit_invoices", schema=None) as batch_op:
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "matched_blockchain_deposit_id",
            new_column_name="matched_binance_deposit_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )

    with op.batch_alter_table("blockchain_deposits", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_blockchain_deposits_txid"))
        batch_op.drop_index(batch_op.f("ix_blockchain_deposits_detected_at"))
        batch_op.drop_index(batch_op.f("ix_blockchain_deposits_external_id"))
        batch_op.drop_constraint(
            batch_op.f("uq_blockchain_deposits_deposit_invoice_id"), type_="unique"
        )
        batch_op.drop_index(batch_op.f("ix_blockchain_deposits_block_number"))
        batch_op.drop_constraint(
            "uq_blockchain_deposit_network_txid_log", type_="unique"
        )
        batch_op.create_unique_constraint(
            "uq_binance_deposit_network_txid", ["network", "txid"]
        )
        batch_op.drop_column("confirmations")
        batch_op.drop_column("token_contract_address")
        batch_op.drop_column("provider")
        batch_op.drop_column("from_address")
        batch_op.drop_column("block_hash")
        batch_op.drop_column("block_number")
        batch_op.drop_column("log_index")
        batch_op.alter_column(
            "asset",
            new_column_name="coin",
            existing_type=sa.String(length=32),
            nullable=False,
        )
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "external_id",
            new_column_name="binance_deposit_id",
            existing_type=sa.String(length=255),
            nullable=False,
        )

    with op.batch_alter_table("blockchain_deposits", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_binance_deposits_deposit_invoice_id", ["deposit_invoice_id"]
        )
        batch_op.create_index(
            "ix_binance_deposits_binance_deposit_id",
            ["binance_deposit_id"],
            unique=True,
        )
        batch_op.create_index(
            "ix_binance_deposits_detected_at", ["detected_at"], unique=False
        )
        batch_op.create_index("ix_binance_deposits_txid", ["txid"], unique=False)
    op.rename_table("blockchain_deposits", "binance_deposits")

    with op.batch_alter_table("deposit_wallets", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_deposit_wallets_monitoring_enabled"))
        batch_op.drop_column("monitoring_enabled")
        batch_op.drop_column("confirmations_required")
        batch_op.drop_column("token_decimals")
        batch_op.drop_column("token_contract_address")
        batch_op.drop_column("token_standard")
        batch_op.drop_column("chain_id")
        batch_op.drop_column("provider_network")
        batch_op.drop_column("provider")
        batch_op.alter_column(
            "network",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=False,
        )
