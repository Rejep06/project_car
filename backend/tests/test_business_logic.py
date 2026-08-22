"""Проверки адресов пополнения, рефералов и календаря вывода."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.models import RewardPayout
from app.db.session import async_session_maker
from app.services.reward_service import RewardService
from app.utils.datetime import get_withdrawal_window, utcnow


def wallet_payload(title: str, address_char: str, sort_order: int) -> dict:
    return {
        "title": title,
        "address": "0x" + address_char * 40,
        "asset": "USDT",
        "network": "ETHEREUM",
        "network_display_name": "Ethereum (ERC-20)",
        "sort_order": sort_order,
        "is_active": True,
    }


@pytest.mark.asyncio
async def test_user_can_choose_one_of_multiple_deposit_wallets(
    client, make_account, admin_account
):
    user = await make_account()
    second_payload = wallet_payload("Резервный адрес", "d", 20)
    first_payload = wallet_payload("Основной адрес", "c", 10)

    second = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=second_payload,
        headers=admin_account["headers"],
    )
    first = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=first_payload,
        headers=admin_account["headers"],
    )
    assert first.status_code == second.status_code == 201

    available = await client.get(
        "/api/v1/wallet/deposit-addresses", headers=user["headers"]
    )
    assert available.status_code == 200, available.text
    assert [item["title"] for item in available.json()] == [
        "Основной адрес",
        "Резервный адрес",
    ]

    selected = second.json()
    invoice = await client.post(
        "/api/v1/wallet/deposits",
        json={"amount": "25.000000", "deposit_wallet_id": selected["id"]},
        headers=user["headers"],
    )
    assert invoice.status_code == 201, invoice.text
    assert invoice.json()["deposit_wallet_id"] == selected["id"]
    assert invoice.json()["wallet_name"] == "Резервный адрес"
    assert invoice.json()["address"] == second_payload["address"]


@pytest.mark.asyncio
async def test_admin_can_add_manual_wallet_for_another_network(
    client, make_account, admin_account
):
    """Любая другая сеть хранится в БД, но без неподключённой автопроверки."""
    user = await make_account()
    payload = {
        "title": "Резервный адрес Solana",
        "address": "7YWHMfk9JZe0LM0g1ManualSolanaWalletAddress123",
        "asset": "USDT",
        "network": "SOLANA",
        "network_display_name": "Solana",
        "provider": "manual",
        "provider_network": None,
        "chain_id": None,
        "token_standard": "SPL",
        "token_contract_address": None,
        "token_decimals": 6,
        "confirmations_required": 32,
        "monitoring_enabled": False,
        "sort_order": 30,
        "is_active": True,
    }
    created = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=payload,
        headers=admin_account["headers"],
    )
    assert created.status_code == 201, created.text
    assert created.json()["monitoring_enabled"] is False
    assert created.json()["network"] == "SOLANA"

    available = await client.get(
        "/api/v1/wallet/deposit-addresses", headers=user["headers"]
    )
    assert any(item["network"] == "SOLANA" for item in available.json())


@pytest.mark.asyncio
async def test_unsupported_network_cannot_enable_infura_monitoring(
    client, admin_account
):
    payload = {
        "title": "Неверная автоматическая сеть",
        "address": "0x" + "e" * 40,
        "asset": "USDT",
        "network": "SOLANA",
        "network_display_name": "Solana",
        "provider": "infura",
        "provider_network": "mainnet",
        "chain_id": 1,
        "token_standard": "ERC20",
        "token_contract_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "token_decimals": 6,
        "confirmations_required": 12,
        "monitoring_enabled": True,
        "sort_order": 40,
        "is_active": True,
    }
    response = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=payload,
        headers=admin_account["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unofficial_usdt_contract_cannot_enable_monitoring(
    client, admin_account
):
    payload = {
        "title": "Поддельный токен",
        "address": "0x" + "f" * 40,
        "asset": "USDT",
        "network": "ETHEREUM",
        "network_display_name": "Ethereum (ERC-20)",
        "provider": "infura",
        "provider_network": "mainnet",
        "chain_id": 1,
        "token_standard": "ERC20",
        "token_contract_address": "0x" + "1" * 40,
        "token_decimals": 6,
        "confirmations_required": 12,
        "monitoring_enabled": True,
        "sort_order": 50,
        "is_active": True,
    }
    response = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=payload,
        headers=admin_account["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_automatic_monitoring_requires_confirmation(client, admin_account):
    payload = wallet_payload("Без подтверждений", "9", 60)
    payload["confirmations_required"] = 0
    response = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=payload,
        headers=admin_account["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_manual_wallet_still_accepts_only_usdt(client, admin_account):
    payload = {
        "title": "Неподдерживаемый актив",
        "address": "AnyNetworkWalletAddress123456789",
        "asset": "USDC",
        "network": "OTHER",
        "network_display_name": "Другая сеть",
        "provider": "manual",
        "provider_network": None,
        "chain_id": None,
        "token_standard": None,
        "token_contract_address": None,
        "token_decimals": 6,
        "confirmations_required": 1,
        "monitoring_enabled": False,
        "sort_order": 70,
        "is_active": True,
    }
    response = await client.post(
        "/api/v1/admin/deposit-wallets",
        json=payload,
        headers=admin_account["headers"],
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_referrer_receives_ten_percent_after_program_activation(
    client, make_account, admin_account, create_plan, credit_balance
):
    referrer = await make_account()
    invited = await make_account(referral_code=referrer["referral_code"].lower())
    assert invited["referred_by_user_id"] == referrer["id"]

    await credit_balance(invited, "100.000000")
    plan = await create_plan(price="50.000000", tier="standard")
    purchase = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**invited["headers"], "Idempotency-Key": "referral-purchase"},
    )
    assert purchase.status_code == 201, purchase.text

    referrer_wallet = await client.get(
        "/api/v1/wallet", headers=referrer["headers"]
    )
    assert referrer_wallet.json()["available_balance"] == "5.000000"

    summary = await client.get("/api/v1/referrals/me", headers=referrer["headers"])
    assert summary.status_code == 200, summary.text
    assert summary.json()["invited_count"] == 1
    assert summary.json()["active_invited_count"] == 1
    assert summary.json()["purchase_bonus_earned"] == "5.000000"
    assert summary.json()["reward_bonus_earned"] == "0.000000"


@pytest.mark.asyncio
async def test_premium_reward_adds_two_usdt_to_referrer(
    client, make_account, admin_account, create_plan, credit_balance
):
    referrer = await make_account()
    invited = await make_account(referral_code=referrer["referral_code"])
    await credit_balance(invited, "100.000000")
    plan = await create_plan(
        title="Премиум Драйв",
        tier="premium",
        price="20.000000",
        reward_amount="3.000000",
        reward_frequency="daily",
        reward_duration_value=1,
        reward_duration_unit="day",
    )
    purchase = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**invited["headers"], "Idempotency-Key": "premium-referral"},
    )
    assert purchase.status_code == 201, purchase.text

    async with async_session_maker() as session:
        payout = await session.scalar(
            select(RewardPayout).where(
                RewardPayout.user_subscription_id == UUID(purchase.json()["id"])
            )
        )
        assert payout is not None
        payout.due_at = utcnow() - timedelta(seconds=1)
        await session.commit()

    assert await RewardService.process_batch(async_session_maker, batch_size=20) == 1
    assert await RewardService.process_batch(async_session_maker, batch_size=20) == 0

    referrer_wallet = await client.get(
        "/api/v1/wallet", headers=referrer["headers"]
    )
    # 10% от 20 USDT при активации + 2 USDT за начисление приглашённого.
    assert referrer_wallet.json()["available_balance"] == "4.000000"

    summary = await client.get("/api/v1/referrals/me", headers=referrer["headers"])
    assert summary.json()["purchase_bonus_earned"] == "2.000000"
    assert summary.json()["reward_bonus_earned"] == "2.000000"
    assert summary.json()["total_earned"] == "4.000000"


def test_withdrawal_window_uses_almaty_wednesday():
    monday = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
    closed = get_withdrawal_window(
        timezone_name="Asia/Almaty", allowed_weekday=2, now=monday
    )
    assert closed.is_open is False
    assert closed.weekday_label == "среду"
    assert closed.next_open_at == datetime(2026, 8, 4, 19, 0, tzinfo=UTC)

    wednesday = datetime(2026, 8, 5, 10, 0, tzinfo=UTC)
    opened = get_withdrawal_window(
        timezone_name="Asia/Almaty", allowed_weekday=2, now=wednesday
    )
    assert opened.is_open is True
    assert opened.next_open_at is None
