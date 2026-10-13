"""Native network retry contracts against the real ASGI API and isolated DB."""

from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.models import Lottery, User
from app.db.session import async_session_maker
from app.services.deposit_wallet_service import DepositWalletService
from app.utils.datetime import utcnow
from tests.test_email_lottery import create_lottery

ADDRESS = "0x" + "b" * 40


@pytest.mark.asyncio
async def test_deposit_retry_preserves_exact_invoice_and_rejects_changed_payload(
    client, make_account, monkeypatch
):
    user = await make_account()
    headers = {**user["headers"], "Idempotency-Key": "mobile-deposit-1"}
    url = "/api/v1/wallet/deposits"
    first = await client.post(url, headers=headers, json={"amount": "20"})
    assert first.status_code == 201, first.text

    async def unavailable_wallet(*_args, **_kwargs):
        raise AssertionError("Replay must not reallocate an invoice or require an active wallet")

    monkeypatch.setattr(DepositWalletService, "get_active", unavailable_wallet)
    retry = await client.post(url, headers=headers, json={"amount": "20.000000"})
    assert retry.status_code == 201, retry.text
    assert retry.json()["id"] == first.json()["id"]
    assert retry.json()["expected_amount"] == first.json()["expected_amount"]
    changed = await client.post(url, headers=headers, json={"amount": "21"})
    assert changed.status_code == 409, changed.text
    assert changed.json()["error"]["code"] == "idempotency_key_conflict"
    invoices = await client.get(url, headers=user["headers"])
    assert invoices.json()["total"] == 1


@pytest.mark.asyncio
async def test_deposit_key_cannot_read_another_users_invoice(client, make_account):
    first_user = await make_account()
    other_user = await make_account()
    url = "/api/v1/wallet/deposits"
    first = await client.post(
        url,
        headers={**first_user["headers"], "Idempotency-Key": "shared-deposit-key"},
        json={"amount": "20"},
    )
    assert first.status_code == 201, first.text
    attack = await client.post(
        url,
        headers={**other_user["headers"], "Idempotency-Key": "shared-deposit-key"},
        json={"amount": "20"},
    )
    assert attack.status_code == 409, attack.text
    assert attack.json()["error"]["code"] == "idempotency_key_conflict"


@pytest.mark.asyncio
async def test_withdrawal_retry_holds_once_and_recovers_after_rejection_and_window_close(
    client, make_account, admin_account, credit_balance, monkeypatch
):
    user = await make_account()
    await credit_balance(user)
    headers = {**user["headers"], "Idempotency-Key": "mobile-withdrawal-1"}
    payload = {"amount": "20", "destination_address": ADDRESS}
    url = "/api/v1/wallet/withdrawals"
    first = await client.post(url, headers=headers, json=payload)
    assert first.status_code == 201, first.text
    retry = await client.post(url, headers=headers, json=payload)
    assert retry.status_code == 201, retry.text
    assert first.json()["id"] == retry.json()["id"]
    assert retry.json()["fee"] == "2.000000"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "78.000000"
    assert wallet.json()["locked_balance"] == "22.000000"
    rejected = await client.post(
        f"/api/v1/admin/withdrawals/{first.json()['id']}/reject",
        headers=admin_account["headers"],
        json={"comment": "Тестовый возврат"},
    )
    assert rejected.status_code == 200, rejected.text

    def no_window_check(**_kwargs):
        raise AssertionError("Committed replay must work outside the withdrawal day")

    monkeypatch.setattr("app.services.withdrawal_service.get_withdrawal_window", no_window_check)
    recovered = await client.post(url, headers=headers, json=payload)
    assert recovered.status_code == 201, recovered.text
    assert recovered.json()["status"] == "rejected"
    assert recovered.json()["id"] == first.json()["id"]
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "100.000000"
    assert wallet.json()["locked_balance"] == "0.000000"


@pytest.mark.asyncio
@pytest.mark.parametrize("changed", [
    {"amount": "21", "destination_address": ADDRESS},
    {"amount": "20", "destination_address": "0x" + "c" * 40},
])
async def test_withdrawal_key_rejects_changed_amount_or_address(
    client, make_account, credit_balance, changed
):
    user = await make_account()
    await credit_balance(user)
    headers = {**user["headers"], "Idempotency-Key": "mobile-withdrawal-conflict"}
    url = "/api/v1/wallet/withdrawals"
    first = await client.post(url, headers=headers, json={"amount": "20", "destination_address": ADDRESS})
    assert first.status_code == 201, first.text
    conflict = await client.post(url, headers=headers, json=changed)
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "idempotency_key_conflict"
    history = await client.get(url, headers=user["headers"])
    assert history.json()["total"] == 1


@pytest.mark.asyncio
async def test_withdrawal_key_cannot_read_another_users_request(
    client, make_account, credit_balance
):
    user = await make_account()
    other = await make_account()
    await credit_balance(user)
    await credit_balance(other)
    payload = {"amount": "20", "destination_address": ADDRESS}
    url = "/api/v1/wallet/withdrawals"
    first = await client.post(url, headers={**user["headers"], "Idempotency-Key": "shared-withdrawal"}, json=payload)
    assert first.status_code == 201, first.text
    attack = await client.post(url, headers={**other["headers"], "Idempotency-Key": "shared-withdrawal"}, json=payload)
    assert attack.status_code == 409, attack.text
    wallet = await client.get("/api/v1/wallet", headers=other["headers"])
    assert wallet.json()["available_balance"] == "100.000000"


@pytest.mark.asyncio
async def test_lottery_retry_recovers_after_sales_close_and_rejects_changed_quantity(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    lottery, _ = await create_lottery(client, admin_account, suffix="Mobile replay", prize_type="physical")
    url = f"/api/v1/lotteries/{lottery['id']}/tickets"
    headers = {**user["headers"], "Idempotency-Key": "mobile-lottery-replay"}
    first = await client.post(url, headers=headers, json={"quantity": 2, "accept_rules": True})
    assert first.status_code == 201, first.text
    async with async_session_maker() as session:
        row = await session.scalar(select(Lottery).where(Lottery.id == UUID(lottery["id"])))
        row.sales_end_at = utcnow() - timedelta(minutes=1)
        row.max_tickets_total = 2
        row.max_tickets_per_user = 2
        await session.commit()
    retry = await client.post(url, headers=headers, json={"quantity": 2, "accept_rules": True})
    assert retry.status_code == 201, retry.text
    assert retry.json()["purchase_id"] == first.json()["purchase_id"]
    changed = await client.post(url, headers=headers, json={"quantity": 1, "accept_rules": True})
    assert changed.status_code == 409, changed.text
    assert changed.json()["error"]["code"] == "idempotency_key_conflict"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"


@pytest.mark.asyncio
async def test_optional_wallet_keys_keep_old_web_requests_compatible(client, make_account, credit_balance):
    user = await make_account()
    await credit_balance(user)
    deposit = await client.post("/api/v1/wallet/deposits", headers=user["headers"], json={"amount": "20"})
    withdrawal = await client.post("/api/v1/wallet/withdrawals", headers=user["headers"], json={"amount": "20", "destination_address": ADDRESS})
    assert deposit.status_code == 201, deposit.text
    assert withdrawal.status_code == 201, withdrawal.text


@pytest.mark.asyncio
async def test_whitespace_idempotency_key_is_rejected(client, make_account):
    user = await make_account()
    response = await client.post("/api/v1/wallet/deposits", headers={**user["headers"], "Idempotency-Key": "   "}, json={"amount": "20"})
    assert response.status_code == 400, response.text
    assert response.json()["error"]["code"] == "invalid_idempotency_key"


@pytest.mark.asyncio
async def test_subscription_replay_recovers_after_freeze_without_second_debit(
    client, make_account, credit_balance, create_plan
):
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan()
    url = f"/api/v1/subscriptions/{plan['id']}/purchase"
    headers = {**user["headers"], "Idempotency-Key": "mobile-subscription-replay"}
    first = await client.post(url, headers=headers)
    assert first.status_code == 201, first.text
    async with async_session_maker() as session:
        row = await session.get(User, UUID(user["id"]))
        row.is_frozen = True
        await session.commit()
    retry = await client.post(url, headers=headers)
    assert retry.status_code == 201, retry.text
    assert retry.json()["id"] == first.json()["id"]
    fresh = await client.post(url, headers={**user["headers"], "Idempotency-Key": "new-after-freeze"})
    assert fresh.status_code == 403, fresh.text
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"


@pytest.mark.asyncio
async def test_public_config_advertises_durable_financial_retry_support(client):
    response = await client.get("/api/v1/system/config")
    assert response.status_code == 200, response.text
    assert response.json()["financial_request_idempotency_supported"] is True


@pytest.mark.asyncio
async def test_native_json_refresh_rotation_and_logout_revoke_refresh(client, make_account):
    user = await make_account()
    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert refreshed.status_code == 200, refreshed.text
    pair = refreshed.json()
    assert pair["refresh_token"] != user["refresh_token"]
    assert pair["access_token"] and pair["expires_in"] > 0
    stale = await client.post("/api/v1/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert stale.status_code == 401, stale.text
    assert stale.json()["error"]["code"] == "invalid_refresh_token"
    logout = await client.post("/api/v1/auth/logout", json={"refresh_token": pair["refresh_token"]})
    assert logout.status_code == 200, logout.text
    revoked = await client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert revoked.status_code == 401, revoked.text


@pytest.mark.asyncio
async def test_max_length_withdrawal_header_fits_ledger_without_truncation(
    client, make_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    headers = {**user["headers"], "Idempotency-Key": "x" * 255}
    payload = {"amount": "20", "destination_address": ADDRESS}
    first = await client.post("/api/v1/wallet/withdrawals", headers=headers, json=payload)
    retry = await client.post("/api/v1/wallet/withdrawals", headers=headers, json=payload)
    assert first.status_code == retry.status_code == 201, (first.text, retry.text)
    assert first.json()["id"] == retry.json()["id"]
