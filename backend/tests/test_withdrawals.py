"""19–23. Hold, refund, complete и уникальность TxID вывода."""

import pytest

ETHEREUM_ADDRESS = "0x" + "b" * 40


async def create_withdrawal(client, user, amount="20.000000"):
    response = await client.post(
        "/api/v1/wallet/withdrawals",
        headers=user["headers"],
        json={"destination_address": ETHEREUM_ADDRESS, "amount": amount},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_withdrawal_moves_money_to_locked(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user)
    assert item["status"] == "pending_review"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "78.000000"
    assert wallet.json()["locked_balance"] == "22.000000"


@pytest.mark.asyncio
async def test_reject_withdrawal_refunds_money(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user)
    response = await client.post(
        f"/api/v1/admin/withdrawals/{item['id']}/reject",
        headers=admin_account["headers"],
        json={"comment": "Проверка отклонена"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "rejected"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "100.000000"
    assert wallet.json()["locked_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_repeated_rejection_does_not_refund_twice(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user)
    url = f"/api/v1/admin/withdrawals/{item['id']}/reject"
    first = await client.post(
        url,
        headers=admin_account["headers"],
        json={"comment": "Первое отклонение"},
    )
    second = await client.post(
        url,
        headers=admin_account["headers"],
        json={"comment": "Повторное отклонение"},
    )
    assert first.status_code == second.status_code == 200
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "100.000000"
    assert wallet.json()["locked_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_complete_withdrawal_reduces_locked_balance(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user)
    approve = await client.post(
        f"/api/v1/admin/withdrawals/{item['id']}/approve",
        headers=admin_account["headers"],
    )
    assert approve.status_code == 200, approve.text
    sent = await client.post(
        f"/api/v1/admin/withdrawals/{item['id']}/mark-sent",
        headers=admin_account["headers"],
        json={
            "txid": "2" * 64,
            "actual_fee": "1.000000",
            "comment": "Отправлено вручную",
        },
    )
    assert sent.status_code == 200, sent.text
    completed = await client.post(
        f"/api/v1/admin/withdrawals/{item['id']}/complete",
        headers=admin_account["headers"],
        json={"comment": "Подтверждено в сети"},
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "completed"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "79.000000"
    assert wallet.json()["locked_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_withdrawal_txid_is_unique(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    first = await create_withdrawal(client, user)
    second = await create_withdrawal(client, user)
    for item in (first, second):
        response = await client.post(
            f"/api/v1/admin/withdrawals/{item['id']}/approve",
            headers=admin_account["headers"],
        )
        assert response.status_code == 200
    txid = "3" * 64
    first_sent = await client.post(
        f"/api/v1/admin/withdrawals/{first['id']}/mark-sent",
        headers=admin_account["headers"],
        json={"txid": txid, "actual_fee": "2.000000", "comment": None},
    )
    second_sent = await client.post(
        f"/api/v1/admin/withdrawals/{second['id']}/mark-sent",
        headers=admin_account["headers"],
        json={"txid": txid, "actual_fee": "2.000000", "comment": None},
    )
    assert first_sent.status_code == 200
    assert second_sent.status_code == 409
    assert second_sent.json()["error"]["code"] == "withdrawal_txid_exists"
