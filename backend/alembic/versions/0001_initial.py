"""Начальная схема базы данных.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-16 22:10:05.955884
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Команды создания схемы, сгенерированные и проверенные через Alembic.
    op.create_table('subscription_plans',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('slug', sa.String(length=200), nullable=False),
    sa.Column('category', sa.Enum('game', 'application', name='plan_category', native_enum=False), nullable=False),
    sa.Column('short_description', sa.String(length=500), nullable=False),
    sa.Column('full_description', sa.Text(), nullable=False),
    sa.Column('image_url', sa.String(length=1000), nullable=True),
    sa.Column('price_atomic', sa.BigInteger(), nullable=False),
    sa.Column('access_duration_value', sa.Integer(), nullable=False),
    sa.Column('access_duration_unit', sa.Enum('day', 'week', 'month', 'year', name='access_duration_unit', native_enum=False), nullable=False),
    sa.Column('reward_amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('reward_frequency', sa.Enum('daily', 'weekly', 'monthly', name='reward_frequency', native_enum=False), nullable=False),
    sa.Column('reward_duration_value', sa.Integer(), nullable=False),
    sa.Column('reward_duration_unit', sa.Enum('day', 'week', 'month', 'year', name='reward_duration_unit', native_enum=False), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_subscription_plans'))
    )
    with op.batch_alter_table('subscription_plans', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_subscription_plans_is_active'), ['is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_subscription_plans_slug'), ['slug'], unique=True)

    op.create_table('users',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('password_hash', sa.String(length=512), nullable=False),
    sa.Column('role', sa.Enum('user', 'admin', name='user_role', native_enum=False), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_frozen', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)

    op.create_table('audit_logs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('admin_user_id', sa.Uuid(), nullable=False),
    sa.Column('action', sa.String(length=100), nullable=False),
    sa.Column('entity_type', sa.String(length=100), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=True),
    sa.Column('old_data', sa.JSON(), nullable=True),
    sa.Column('new_data', sa.JSON(), nullable=True),
    sa.Column('ip_address', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], name=op.f('fk_audit_logs_admin_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_audit_logs_action'), ['action'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_admin_user_id'), ['admin_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_entity_type'), ['entity_type'], unique=False)

    op.create_table('auth_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_auth_sessions_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_auth_sessions')),
    sa.UniqueConstraint('refresh_token_hash', name=op.f('uq_auth_sessions_refresh_token_hash'))
    )
    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_auth_sessions_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_auth_sessions_user_id'), ['user_id'], unique=False)

    op.create_table('deposit_invoices',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('requested_amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('expected_amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('received_amount_atomic', sa.BigInteger(), nullable=True),
    sa.Column('asset', sa.String(length=16), nullable=False),
    sa.Column('network', sa.String(length=32), nullable=False),
    sa.Column('deposit_address', sa.String(length=256), nullable=False),
    sa.Column('status', sa.Enum('waiting', 'detected', 'credited', 'expired', 'manual_review', 'cancelled', name='deposit_invoice_status', native_enum=False), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('amount_reserved_until', sa.DateTime(timezone=True), nullable=False),
    sa.Column('matched_binance_deposit_id', sa.Uuid(), nullable=True),
    sa.Column('credited_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_deposit_invoices_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_deposit_invoices'))
    )
    with op.batch_alter_table('deposit_invoices', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_deposit_invoices_amount_reserved_until'), ['amount_reserved_until'], unique=False)
        batch_op.create_index(batch_op.f('ix_deposit_invoices_expected_amount_atomic'), ['expected_amount_atomic'], unique=False)
        batch_op.create_index(batch_op.f('ix_deposit_invoices_expires_at'), ['expires_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_deposit_invoices_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_deposit_invoices_user_id'), ['user_id'], unique=False)

    op.create_table('posts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('author_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=250), nullable=False),
    sa.Column('slug', sa.String(length=250), nullable=False),
    sa.Column('excerpt', sa.String(length=1000), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('cover_image_url', sa.String(length=1000), nullable=True),
    sa.Column('status', sa.Enum('draft', 'published', 'archived', name='post_status', native_enum=False), nullable=False),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_posts_author_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_posts'))
    )
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_posts_published_at'), ['published_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_posts_slug'), ['slug'], unique=True)
        batch_op.create_index(batch_op.f('ix_posts_status'), ['status'], unique=False)

    op.create_table('user_subscriptions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('plan_id', sa.Uuid(), nullable=False),
    sa.Column('status', sa.Enum('active', 'expired', 'cancelled', name='user_subscription_status', native_enum=False), nullable=False),
    sa.Column('purchased_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('access_started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('access_ends_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('price_atomic', sa.BigInteger(), nullable=False),
    sa.Column('reward_amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('reward_frequency', sa.Enum('daily', 'weekly', 'monthly', name='purchased_reward_frequency', native_enum=False), nullable=False),
    sa.Column('reward_duration_value', sa.Integer(), nullable=False),
    sa.Column('reward_duration_unit', sa.Enum('day', 'week', 'month', 'year', name='purchased_reward_duration_unit', native_enum=False), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], name=op.f('fk_user_subscriptions_plan_id_subscription_plans'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_subscriptions_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_subscriptions'))
    )
    with op.batch_alter_table('user_subscriptions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_subscriptions_access_ends_at'), ['access_ends_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_subscriptions_plan_id'), ['plan_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_subscriptions_user_id'), ['user_id'], unique=False)

    op.create_table('wallets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('asset', sa.String(length=16), nullable=False),
    sa.Column('available_balance_atomic', sa.BigInteger(), nullable=False),
    sa.Column('locked_balance_atomic', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('available_balance_atomic >= 0', name=op.f('ck_wallets_available_nonnegative')),
    sa.CheckConstraint('locked_balance_atomic >= 0', name=op.f('ck_wallets_locked_nonnegative')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_wallets_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wallets')),
    sa.UniqueConstraint('user_id', name=op.f('uq_wallets_user_id'))
    )
    op.create_table('withdrawal_requests',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('asset', sa.String(length=16), nullable=False),
    sa.Column('network', sa.String(length=32), nullable=False),
    sa.Column('destination_address', sa.String(length=256), nullable=False),
    sa.Column('amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('fee_atomic', sa.BigInteger(), nullable=False),
    sa.Column('total_debit_atomic', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('pending_review', 'approved', 'sent', 'completed', 'rejected', 'cancelled', name='withdrawal_status', native_enum=False), nullable=False),
    sa.Column('admin_comment', sa.Text(), nullable=True),
    sa.Column('txid', sa.String(length=255), nullable=True),
    sa.Column('approved_by_admin_id', sa.Uuid(), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['approved_by_admin_id'], ['users.id'], name=op.f('fk_withdrawal_requests_approved_by_admin_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_withdrawal_requests_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_withdrawal_requests'))
    )
    with op.batch_alter_table('withdrawal_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_withdrawal_requests_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_withdrawal_requests_txid'), ['txid'], unique=True)
        batch_op.create_index(batch_op.f('ix_withdrawal_requests_user_id'), ['user_id'], unique=False)

    op.create_table('binance_deposits',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('binance_deposit_id', sa.String(length=255), nullable=False),
    sa.Column('txid', sa.String(length=255), nullable=False),
    sa.Column('address', sa.String(length=256), nullable=False),
    sa.Column('coin', sa.String(length=32), nullable=False),
    sa.Column('network', sa.String(length=32), nullable=False),
    sa.Column('amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Enum('pending', 'success', 'rejected', 'credited_locked', 'wrong_deposit', 'waiting_confirmation', 'unknown', name='binance_deposit_status', native_enum=False), nullable=False),
    sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('raw_data', sa.JSON(), nullable=False),
    sa.Column('deposit_invoice_id', sa.Uuid(), nullable=True),
    sa.Column('credited_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['deposit_invoice_id'], ['deposit_invoices.id'], name=op.f('fk_binance_deposits_deposit_invoice_id_deposit_invoices'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_binance_deposits')),
    sa.UniqueConstraint('deposit_invoice_id', name=op.f('uq_binance_deposits_deposit_invoice_id')),
    sa.UniqueConstraint('network', 'txid', name='uq_binance_deposit_network_txid')
    )
    with op.batch_alter_table('binance_deposits', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_binance_deposits_binance_deposit_id'), ['binance_deposit_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_binance_deposits_detected_at'), ['detected_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_binance_deposits_txid'), ['txid'], unique=False)

    op.create_table('deposit_amount_reservations',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('invoice_id', sa.Uuid(), nullable=False),
    sa.Column('expected_amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('reserved_until', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['invoice_id'], ['deposit_invoices.id'], name=op.f('fk_deposit_amount_reservations_invoice_id_deposit_invoices'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_deposit_amount_reservations')),
    sa.UniqueConstraint('expected_amount_atomic', name=op.f('uq_deposit_amount_reservations_expected_amount_atomic')),
    sa.UniqueConstraint('invoice_id', name=op.f('uq_deposit_amount_reservations_invoice_id'))
    )
    with op.batch_alter_table('deposit_amount_reservations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_deposit_amount_reservations_reserved_until'), ['reserved_until'], unique=False)

    op.create_table('wallet_transactions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('wallet_id', sa.Uuid(), nullable=False),
    sa.Column('operation_type', sa.Enum('deposit_credit', 'subscription_purchase', 'reward_credit', 'withdrawal_hold', 'withdrawal_complete', 'withdrawal_refund', 'admin_adjustment', name='wallet_operation_type', native_enum=False), nullable=False),
    sa.Column('available_delta_atomic', sa.BigInteger(), nullable=False),
    sa.Column('locked_delta_atomic', sa.BigInteger(), nullable=False),
    sa.Column('available_after_atomic', sa.BigInteger(), nullable=False),
    sa.Column('locked_after_atomic', sa.BigInteger(), nullable=False),
    sa.Column('idempotency_key', sa.String(length=255), nullable=False),
    sa.Column('related_entity_type', sa.String(length=64), nullable=True),
    sa.Column('related_entity_id', sa.Uuid(), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('metadata_json', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('available_after_atomic >= 0', name=op.f('ck_wallet_transactions_available_after_nonnegative')),
    sa.CheckConstraint('locked_after_atomic >= 0', name=op.f('ck_wallet_transactions_locked_after_nonnegative')),
    sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], name=op.f('fk_wallet_transactions_wallet_id_wallets'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_wallet_transactions'))
    )
    with op.batch_alter_table('wallet_transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_wallet_transactions_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_wallet_transactions_idempotency_key'), ['idempotency_key'], unique=True)
        batch_op.create_index(batch_op.f('ix_wallet_transactions_wallet_id'), ['wallet_id'], unique=False)

    op.create_table('reward_payouts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_subscription_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('pending', 'processing', 'paid', 'failed', 'cancelled', name='reward_payout_status', native_enum=False), nullable=False),
    sa.Column('wallet_transaction_id', sa.Uuid(), nullable=True),
    sa.Column('attempt_count', sa.Integer(), nullable=False),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_reward_payouts_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_subscription_id'], ['user_subscriptions.id'], name=op.f('fk_reward_payouts_user_subscription_id_user_subscriptions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['wallet_transaction_id'], ['wallet_transactions.id'], name=op.f('fk_reward_payouts_wallet_transaction_id_wallet_transactions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reward_payouts'))
    )
    with op.batch_alter_table('reward_payouts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reward_payouts_due_at'), ['due_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_reward_payouts_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_reward_payouts_user_id'), ['user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_reward_payouts_user_subscription_id'), ['user_subscription_id'], unique=False)

    op.create_table('unmatched_deposits',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('binance_deposit_id', sa.Uuid(), nullable=False),
    sa.Column('txid', sa.String(length=255), nullable=False),
    sa.Column('amount_atomic', sa.BigInteger(), nullable=False),
    sa.Column('address', sa.String(length=256), nullable=False),
    sa.Column('network', sa.String(length=32), nullable=False),
    sa.Column('reason', sa.Enum('wrong_amount', 'expired_invoice', 'invoice_not_found', 'duplicate_candidate', 'unknown', name='unmatched_deposit_reason', native_enum=False), nullable=False),
    sa.Column('status', sa.Enum('unresolved', 'assigned', 'ignored', name='unmatched_deposit_status', native_enum=False), nullable=False),
    sa.Column('assigned_user_id', sa.Uuid(), nullable=True),
    sa.Column('assigned_invoice_id', sa.Uuid(), nullable=True),
    sa.Column('assigned_by_admin_id', sa.Uuid(), nullable=True),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['assigned_by_admin_id'], ['users.id'], name=op.f('fk_unmatched_deposits_assigned_by_admin_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['assigned_invoice_id'], ['deposit_invoices.id'], name=op.f('fk_unmatched_deposits_assigned_invoice_id_deposit_invoices'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['assigned_user_id'], ['users.id'], name=op.f('fk_unmatched_deposits_assigned_user_id_users'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['binance_deposit_id'], ['binance_deposits.id'], name=op.f('fk_unmatched_deposits_binance_deposit_id_binance_deposits'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_unmatched_deposits')),
    sa.UniqueConstraint('binance_deposit_id', name=op.f('uq_unmatched_deposits_binance_deposit_id'))
    )
    with op.batch_alter_table('unmatched_deposits', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_unmatched_deposits_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_unmatched_deposits_txid'), ['txid'], unique=False)

    op.create_table('support_tickets',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('category', sa.Enum('deposit_problem', 'withdrawal_problem', 'subscription_problem', 'other', name='support_ticket_category', native_enum=False), nullable=False),
    sa.Column('subject', sa.String(length=250), nullable=False),
    sa.Column('status', sa.Enum('open', 'in_review', 'waiting_user', 'resolved', 'closed', name='support_ticket_status', native_enum=False), nullable=False),
    sa.Column('related_deposit_invoice_id', sa.Uuid(), nullable=True),
    sa.Column('related_binance_deposit_id', sa.Uuid(), nullable=True),
    sa.Column('related_unmatched_deposit_id', sa.Uuid(), nullable=True),
    sa.Column('txid_conflict', sa.Boolean(), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['related_binance_deposit_id'], ['binance_deposits.id'], name=op.f('fk_support_tickets_related_binance_deposit_id_binance_deposits'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['related_deposit_invoice_id'], ['deposit_invoices.id'], name=op.f('fk_support_tickets_related_deposit_invoice_id_deposit_invoices'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['related_unmatched_deposit_id'], ['unmatched_deposits.id'], name=op.f('fk_support_tickets_related_unmatched_deposit_id_unmatched_deposits'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_support_tickets_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_tickets'))
    )
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_tickets_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_tickets_user_id'), ['user_id'], unique=False)

    op.create_table('support_messages',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('ticket_id', sa.Uuid(), nullable=False),
    sa.Column('author_user_id', sa.Uuid(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('txid', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['author_user_id'], ['users.id'], name=op.f('fk_support_messages_author_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], name=op.f('fk_support_messages_ticket_id_support_tickets'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_messages'))
    )
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_messages_ticket_id'), ['ticket_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_messages_txid'), ['txid'], unique=False)

    op.create_table('support_attachments',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('message_id', sa.Uuid(), nullable=False),
    sa.Column('original_filename', sa.String(length=255), nullable=False),
    sa.Column('stored_filename', sa.String(length=255), nullable=False),
    sa.Column('mime_type', sa.String(length=100), nullable=False),
    sa.Column('size_bytes', sa.BigInteger(), nullable=False),
    sa.Column('file_path', sa.String(length=1000), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['message_id'], ['support_messages.id'], name=op.f('fk_support_attachments_message_id_support_messages'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_attachments')),
    sa.UniqueConstraint('stored_filename', name=op.f('uq_support_attachments_stored_filename'))
    )
    with op.batch_alter_table('support_attachments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_attachments_message_id'), ['message_id'], unique=False)

    # Конец команд изменения схемы.


def downgrade() -> None:
    # Команды создания схемы, сгенерированные и проверенные через Alembic.
    with op.batch_alter_table('support_attachments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_attachments_message_id'))

    op.drop_table('support_attachments')
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_messages_txid'))
        batch_op.drop_index(batch_op.f('ix_support_messages_ticket_id'))

    op.drop_table('support_messages')
    with op.batch_alter_table('support_tickets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_tickets_user_id'))
        batch_op.drop_index(batch_op.f('ix_support_tickets_status'))

    op.drop_table('support_tickets')
    with op.batch_alter_table('unmatched_deposits', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_unmatched_deposits_txid'))
        batch_op.drop_index(batch_op.f('ix_unmatched_deposits_status'))

    op.drop_table('unmatched_deposits')
    with op.batch_alter_table('reward_payouts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reward_payouts_user_subscription_id'))
        batch_op.drop_index(batch_op.f('ix_reward_payouts_user_id'))
        batch_op.drop_index(batch_op.f('ix_reward_payouts_status'))
        batch_op.drop_index(batch_op.f('ix_reward_payouts_due_at'))

    op.drop_table('reward_payouts')
    with op.batch_alter_table('wallet_transactions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wallet_transactions_wallet_id'))
        batch_op.drop_index(batch_op.f('ix_wallet_transactions_idempotency_key'))
        batch_op.drop_index(batch_op.f('ix_wallet_transactions_created_at'))

    op.drop_table('wallet_transactions')
    with op.batch_alter_table('deposit_amount_reservations', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_deposit_amount_reservations_reserved_until'))

    op.drop_table('deposit_amount_reservations')
    with op.batch_alter_table('binance_deposits', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_binance_deposits_txid'))
        batch_op.drop_index(batch_op.f('ix_binance_deposits_detected_at'))
        batch_op.drop_index(batch_op.f('ix_binance_deposits_binance_deposit_id'))

    op.drop_table('binance_deposits')
    with op.batch_alter_table('withdrawal_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_withdrawal_requests_user_id'))
        batch_op.drop_index(batch_op.f('ix_withdrawal_requests_txid'))
        batch_op.drop_index(batch_op.f('ix_withdrawal_requests_status'))

    op.drop_table('withdrawal_requests')
    op.drop_table('wallets')
    with op.batch_alter_table('user_subscriptions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_subscriptions_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_subscriptions_plan_id'))
        batch_op.drop_index(batch_op.f('ix_user_subscriptions_access_ends_at'))

    op.drop_table('user_subscriptions')
    with op.batch_alter_table('posts', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_posts_status'))
        batch_op.drop_index(batch_op.f('ix_posts_slug'))
        batch_op.drop_index(batch_op.f('ix_posts_published_at'))

    op.drop_table('posts')
    with op.batch_alter_table('deposit_invoices', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_deposit_invoices_user_id'))
        batch_op.drop_index(batch_op.f('ix_deposit_invoices_status'))
        batch_op.drop_index(batch_op.f('ix_deposit_invoices_expires_at'))
        batch_op.drop_index(batch_op.f('ix_deposit_invoices_expected_amount_atomic'))
        batch_op.drop_index(batch_op.f('ix_deposit_invoices_amount_reserved_until'))

    op.drop_table('deposit_invoices')
    with op.batch_alter_table('auth_sessions', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_auth_sessions_user_id'))
        batch_op.drop_index(batch_op.f('ix_auth_sessions_expires_at'))

    op.drop_table('auth_sessions')
    with op.batch_alter_table('audit_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audit_logs_entity_type'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_created_at'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_admin_user_id'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_action'))

    op.drop_table('audit_logs')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    with op.batch_alter_table('subscription_plans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subscription_plans_slug'))
        batch_op.drop_index(batch_op.f('ix_subscription_plans_is_active'))

    op.drop_table('subscription_plans')
    # Конец команд изменения схемы.
