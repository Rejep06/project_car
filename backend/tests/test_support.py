"""14–18. Обращения, вложения, доступ и ручное зачисление."""

import pytest

from app.core.config import get_settings
from app.db.session import async_session_maker
from app.utils.datetime import utcnow
from app.utils.money import format_amount, parse_amount
from app.workers.deposit_worker import run_deposit_cycle
from tests.fakes import FakeInfuraClient, make_deposit


async def prepare_unmatched(client, user, admin_account, suffix: str):
    settings = get_settings()
    invoice = (
        await client.post(
            "/api/v1/wallet/deposits",
            json={"amount": "100.000000"},
            headers=user["headers"],
        )
    ).json()
    actual_atomic = parse_amount(invoice["expected_amount"]) + 7
    txid = "0x" + suffix * 64
    deposit = make_deposit(
        external_id=f"problem-{suffix}",
        txid=txid,
        address=settings.default_deposit_address,
        amount_atomic=actual_atomic,
        detected_at=utcnow(),
    )
    await run_deposit_cycle(
        session_factory=async_session_maker,
        settings=settings,
        client_factory=lambda _settings, _provider_network: FakeInfuraClient([deposit]),
    )
    unmatched = (
        await client.get(
            "/api/v1/admin/deposits/unmatched", headers=admin_account["headers"]
        )
    ).json()["items"][0]
    return invoice, unmatched, txid, actual_atomic


@pytest.mark.asyncio
async def test_user_creates_ticket_with_txid(client, make_account):
    user = await make_account()
    response = await client.post(
        "/api/v1/support/tickets",
        headers=user["headers"],
        json={
            "category": "deposit_problem",
            "subject": "Пополнение не зачислено",
            "message": "Транзакция успешна, но баланс не изменился",
            "txid": "0x" + "e" * 64,
            "related_deposit_invoice_id": None,
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["messages"][0]["txid"] == "0x" + "e" * 64
    assert response.json()["status"] == "open"


@pytest.mark.asyncio
async def test_user_uploads_screenshot(client, make_account):
    user = await make_account()
    ticket = (
        await client.post(
            "/api/v1/support/tickets",
            headers=user["headers"],
            json={
                "category": "other",
                "subject": "Нужна помощь",
                "message": "Прикладываю изображение",
                "txid": None,
                "related_deposit_invoice_id": None,
            },
        )
    ).json()
    message_id = ticket["messages"][0]["id"]
    png = b"\x89PNG\r\n\x1a\n" + b"test-image-content"
    response = await client.post(
        f"/api/v1/support/messages/{message_id}/attachments",
        headers=user["headers"],
        files=[("files", ("proof.png", png, "image/png"))],
    )
    assert response.status_code == 201, response.text
    attachment = response.json()[0]
    assert attachment["original_filename"] == "proof.png"
    assert "file_path" not in attachment
    download = await client.get(
        attachment["download_url"], headers=user["headers"]
    )
    assert download.status_code == 200
    assert download.content == png


@pytest.mark.asyncio
async def test_user_cannot_see_foreign_ticket(client, make_account):
    owner = await make_account("owner@example.com")
    stranger = await make_account("stranger@example.com")
    ticket = (
        await client.post(
            "/api/v1/support/tickets",
            headers=owner["headers"],
            json={
                "category": "other",
                "subject": "Частное обращение",
                "message": "Только владелец",
                "txid": None,
                "related_deposit_invoice_id": None,
            },
        )
    ).json()
    response = await client.get(
        f"/api/v1/support/tickets/{ticket['id']}", headers=stranger["headers"]
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_resolves_problem_deposit_from_ticket(
    client, make_account, admin_account
):
    user = await make_account()
    invoice, _, txid, actual_atomic = await prepare_unmatched(
        client, user, admin_account, "f"
    )
    ticket = (
        await client.post(
            "/api/v1/support/tickets",
            headers=user["headers"],
            json={
                "category": "deposit_problem",
                "subject": "Неверная сумма",
                "message": "Прошу проверить фактическую сумму",
                "txid": txid,
                "related_deposit_invoice_id": invoice["id"],
            },
        )
    ).json()
    admin_detail = await client.get(
        f"/api/v1/admin/support/tickets/{ticket['id']}",
        headers=admin_account["headers"],
    )
    assert admin_detail.status_code == 200, admin_detail.text
    detail = admin_detail.json()
    assert detail["expected_amount"] == invoice["expected_amount"]
    assert detail["actual_amount"] == format_amount(actual_atomic)
    assert detail["deposit_txid"] == txid
    assert detail["deposit_network"] == "ETHEREUM"
    assert detail["deposit_status"] == "success"
    assert detail["deposit_raw_data"]["transactionHash"] == txid

    response = await client.post(
        f"/api/v1/admin/support/tickets/{ticket['id']}/resolve-deposit",
        headers=admin_account["headers"],
        json={"invoice_id": invoice["id"]},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "resolved"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == format_amount(actual_atomic)


@pytest.mark.asyncio
async def test_manual_credit_cannot_run_twice(client, make_account, admin_account):
    user = await make_account()
    invoice, unmatched, _, actual_atomic = await prepare_unmatched(
        client, user, admin_account, "1"
    )
    payload = {"user_id": user["id"], "invoice_id": invoice["id"]}
    url = f"/api/v1/admin/deposits/unmatched/{unmatched['id']}/assign"
    first = await client.post(url, headers=admin_account["headers"], json=payload)
    second = await client.post(url, headers=admin_account["headers"], json=payload)
    assert first.status_code == second.status_code == 200
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == format_amount(actual_atomic)
