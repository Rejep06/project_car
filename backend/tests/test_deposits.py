"""Заявки на пополнение и идемпотентная обработка USDT ERC-20 через Infura."""

from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.utils.datetime import utcnow
from app.utils.money import parse_amount
from app.workers.deposit_worker import run_deposit_cycle
from tests.fakes import FakeInfuraClient, make_deposit


async def run_fake_cycle(fake: FakeInfuraClient) -> int:
    settings = get_settings()
    return await run_deposit_cycle(
        session_factory=async_session_maker,
        settings=settings,
        client_factory=lambda _settings, _provider_network: fake,
    )


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
    assert body["network"] == "Ethereum (ERC-20)"
    assert body["address"] == "0x" + "a" * 40
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
async def test_confirmed_infura_transfer_is_credited(client, make_account):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "100.000000"},
            headers=user["headers"],
        )
    ).json()
    transfer = make_deposit(
        external_id="ethereum:transfer-1:0",
        txid="a" * 64,
        address=settings.default_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow(),
    )
    processed = await run_fake_cycle(FakeInfuraClient([transfer]))
    assert processed == 1
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == invoice["expected_amount"]


@pytest.mark.asyncio
async def test_same_blockchain_event_is_not_credited_twice(client, make_account):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "50.000000"},
            headers=user["headers"],
        )
    ).json()
    transfer = make_deposit(
        external_id="ethereum:same-event:3",
        txid="b" * 64,
        log_index=3,
        address=settings.default_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow(),
    )
    fake = FakeInfuraClient([transfer])
    await run_fake_cycle(fake)
    await run_fake_cycle(fake)
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == invoice["expected_amount"]


@pytest.mark.asyncio
async def test_two_transfer_logs_in_same_transaction_are_processed_separately(
    client, make_account
):
    """У одной Ethereum-транзакции может быть несколько событий Transfer."""
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
    transfers = [
        make_deposit(
            external_id="ethereum:shared-tx:0",
            txid=txid,
            log_index=0,
            address=settings.default_deposit_address,
            amount_atomic=parse_amount(invoice1["expected_amount"]),
            detected_at=utcnow(),
        ),
        make_deposit(
            external_id="ethereum:shared-tx:1",
            txid=txid,
            log_index=1,
            address=settings.default_deposit_address,
            amount_atomic=parse_amount(invoice2["expected_amount"]),
            detected_at=utcnow(),
        ),
    ]
    processed = await run_fake_cycle(FakeInfuraClient(transfers))
    assert processed == 2
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    expected = parse_amount(invoice1["expected_amount"]) + parse_amount(
        invoice2["expected_amount"]
    )
    assert parse_amount(wallet.json()["available_balance"]) == expected


@pytest.mark.asyncio
async def test_transfer_without_required_confirmations_is_not_credited(
    client, make_account
):
    settings = get_settings()
    user = await make_account()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "40.000000"},
            headers=user["headers"],
        )
    ).json()
    transfer = make_deposit(
        external_id="ethereum:unconfirmed:0",
        txid="e" * 64,
        address=settings.default_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        confirmations=5,
        detected_at=utcnow(),
    )
    processed = await run_fake_cycle(FakeInfuraClient([transfer]))
    assert processed == 0
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "0.000000"


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
    transfer = make_deposit(
        external_id="ethereum:wrong-amount:0",
        txid="d" * 64,
        address=settings.default_deposit_address,
        amount_atomic=wrong_amount,
        detected_at=utcnow(),
    )
    await run_fake_cycle(FakeInfuraClient([transfer]))
    response = await client.get(
        "/api/v1/admin/deposits/unmatched", headers=admin_account["headers"]
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1
    item = response.json()["items"][0]
    assert item["reason"] == "wrong_amount"
    assert item["provider"] == "infura"
    assert item["network"] == "ETHEREUM"
    assert item["log_index"] == 0
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_transfer_created_before_invoice_is_not_auto_matched(
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
    transfer = make_deposit(
        external_id="ethereum:before-invoice:0",
        txid="9" * 64,
        address=settings.default_deposit_address,
        amount_atomic=parse_amount(invoice["expected_amount"]),
        detected_at=utcnow() - timedelta(days=1),
    )
    processed = await run_fake_cycle(FakeInfuraClient([transfer]))
    assert processed == 0
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "0.000000"
    unmatched = await client.get(
        "/api/v1/admin/deposits/unmatched", headers=admin_account["headers"]
    )
    assert unmatched.json()["items"][0]["reason"] == "invoice_not_found"
