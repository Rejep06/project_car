"""8–13. Уникальные invoice и идемпотентная Binance-обработка."""

from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.utils.datetime import utcnow
from app.utils.money import parse_amount
from app.workers.deposit_worker import run_deposit_cycle
from tests.fakes import FakeBinanceClient, make_deposit


@pytest.mark.asyncio
async def test_create_deposit_invoice(client, make_account):
    user = await make_account()
    response = await client.post(
        "/api/v1/wallet/deposits",
        json={"amount": "100.000000"},
        headers=user["headers"],
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["requested_amount"] == "100.000000"
    assert body["expected_amount"].startswith("100.")
    assert body["expected_amount"] != body["requested_amount"]
    assert body["network"] == "TRON (TRC20)"
    assert "точную сумму" in body["warning"]


@pytest.mark.asyncio
async def test_active_invoices_have_unique_amounts(client, make_account):
    user = await make_account()
    first = await client.post(
        "/api/v1/wallet/deposits",
        json={"amount": "100.000000"},
        headers=user["headers"],
    )
    second = await client.post(
        "/api/v1/wallet/deposits",
        json={"amount": "100.000000"},
        headers=user["headers"],
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["expected_amount"] != second.json()["expected_amount"]


@pytest.mark.asyncio
async def test_successful_binance_deposit_is_credited(client, make_account):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "100.000000"},
            headers=user["headers"],
        )
    ).json()
    deposit = make_deposit(
        external_id="binance-deposit-1",
        txid="a" * 64,
        address=settings.binance_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow(),
    )
    processed = await run_deposit_cycle(
        client=FakeBinanceClient([deposit]),
        session_factory=async_session_maker,
        settings=settings,
    )
    assert processed == 1
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == invoice["expected_amount"]


@pytest.mark.asyncio
async def test_same_binance_deposit_id_is_not_credited_twice(client, make_account):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "50.000000"},
            headers=user["headers"],
        )
    ).json()
    deposit = make_deposit(
        external_id="same-external-id",
        txid="b" * 64,
        address=settings.binance_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow(),
    )
    fake = FakeBinanceClient([deposit])
    await run_deposit_cycle(
        client=fake, session_factory=async_session_maker, settings=settings
    )
    await run_deposit_cycle(
        client=fake, session_factory=async_session_maker, settings=settings
    )
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == invoice["expected_amount"]


@pytest.mark.asyncio
async def test_same_txid_is_not_credited_twice(client, make_account):
    settings = get_settings()
    user = await make_account()
    invoice1 = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "20.000000"},
            headers=user["headers"],
        )
    ).json()
    invoice2 = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "30.000000"},
            headers=user["headers"],
        )
    ).json()
    txid = "c" * 64
    deposits = [
        make_deposit(
            external_id="txid-first",
            txid=txid,
            address=settings.binance_deposit_address,
            amount_atomic=parse_amount(invoice1["expected_amount"]),
            detected_at=utcnow(),
        ),
        make_deposit(
            external_id="txid-second",
            txid=txid,
            address=settings.binance_deposit_address,
            amount_atomic=parse_amount(invoice2["expected_amount"]),
            detected_at=utcnow(),
        ),
    ]
    await run_deposit_cycle(
        client=FakeBinanceClient(deposits),
        session_factory=async_session_maker,
        settings=settings,
    )
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == invoice1["expected_amount"]


@pytest.mark.asyncio
async def test_wrong_amount_becomes_unmatched(client, make_account, admin_account):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "100.000000"},
            headers=user["headers"],
        )
    ).json()
    wrong_amount = parse_amount(invoice["expected_amount"]) + 1
    deposit = make_deposit(
        external_id="wrong-amount-deposit",
        txid="d" * 64,
        address=settings.binance_deposit_address,
        amount_atomic=wrong_amount,
        detected_at=utcnow(),
    )
    await run_deposit_cycle(
        client=FakeBinanceClient([deposit]),
        session_factory=async_session_maker,
        settings=settings,
    )
    response = await client.get(
        "/api/v1/admin/deposits/unmatched", headers=admin_account["headers"]
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["reason"] == "wrong_amount"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_deposit_created_before_invoice_is_not_auto_matched(
    client, make_account, admin_account
):
    """Старый перевод с совпавшей суммой нельзя назначить новой заявке."""
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "100.000000"},
            headers=user["headers"],
        )
    ).json()
    deposit = make_deposit(
        external_id="deposit-before-invoice",
        txid="9" * 64,
        address=settings.binance_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow() - timedelta(days=1),
    )
    processed = await run_deposit_cycle(
        client=FakeBinanceClient([deposit]),
        session_factory=async_session_maker,
        settings=settings,
    )
    assert processed == 0
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "0.000000"
    unmatched = await client.get(
        "/api/v1/admin/deposits/unmatched", headers=admin_account["headers"]
    )
    assert unmatched.json()["items"][0]["reason"] == "invoice_not_found"
