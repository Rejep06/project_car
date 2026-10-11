"""Административные исправления не нарушают баланс и историю операций."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.db.enums import WalletOperationType
from app.db.models import AuditLog, WalletTransaction
from app.db.session import async_session_maker
from app.services.audit_service import AuditService
from app.services.wallet_service import WalletService
from tests.test_withdrawals import create_withdrawal


async def advance_withdrawal(client, admin_account, item, status, actual_fee="1.000000"):
    base = f"/api/v1/admin/withdrawals/{item['id']}"
    if status in {"approved", "sent", "completed"}:
        response = await client.post(base + "/approve", headers=admin_account["headers"])
        assert response.status_code == 200, response.text
        item = response.json()
    if status in {"sent", "completed"}:
        response = await client.post(
            base + "/mark-sent",
            headers=admin_account["headers"],
            json={"txid": uuid4().hex * 2, "actual_fee": actual_fee},
        )
        assert response.status_code == 200, response.text
        item = response.json()
    if status == "completed":
        response = await client.post(base + "/complete", headers=admin_account["headers"], json={})
        assert response.status_code == 200, response.text
        item = response.json()
    return item


def adjustment_payload(item, amount="60.000000", fee="6.000000"):
    return {
        "amount": amount,
        "fee": fee,
        "comment": "Исправлена ошибочно указанная сумма",
        "expected_updated_at": item["updated_at"],
    }


async def adjust(client, admin_account, item, amount="60.000000", fee="6.000000", *, key=None):
    return await client.patch(
        f"/api/v1/admin/withdrawals/{item['id']}/amounts",
        headers={**admin_account["headers"], "Idempotency-Key": key or str(uuid4())},
        json=adjustment_payload(item, amount, fee),
    )


async def correction_records(item):
    async with async_session_maker() as session:
        audit = list((await session.scalars(
            select(AuditLog).where(
                AuditLog.entity_id == UUID(item["id"]),
                AuditLog.action == "withdrawal_amounts_updated",
            )
        )).all())
        transactions = list((await session.scalars(
            select(WalletTransaction).where(
                WalletTransaction.related_entity_id == UUID(item["id"]),
                WalletTransaction.idempotency_key.like("withdrawal:amounts:%"),
            )
        )).all())
    return audit, transactions


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending_review", "approved", "sent"])
async def test_open_withdrawal_correction_moves_hold_and_later_settles_once(
    client, make_account, admin_account, credit_balance, status
):
    user = await make_account()
    await credit_balance(user, "1000.000000")
    item = await create_withdrawal(client, user, "50")
    item = await advance_withdrawal(client, admin_account, item, status)
    # У sent комиссия уже 1, но до завершения удерживается исходная сумма 55.
    response = await adjust(client, admin_account, item)
    assert response.status_code == 200, response.text
    corrected = response.json()
    assert corrected["amount"] == "60.000000"
    assert corrected["fee"] == "6.000000"
    assert corrected["held_total"] == corrected["final_total"] == "66.000000"
    assert corrected["status"] == status
    assert corrected["user_id"] == user["id"]
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "934.000000"
    assert wallet["locked_balance"] == "66.000000"

    if status == "pending_review":
        end_url = f"/api/v1/wallet/withdrawals/{item['id']}/cancel"
        end_headers, body = user["headers"], {}
    elif status == "approved":
        end_url = f"/api/v1/admin/withdrawals/{item['id']}/reject"
        end_headers, body = admin_account["headers"], {"comment": "Возврат после исправления"}
    else:
        end_url = f"/api/v1/admin/withdrawals/{item['id']}/complete"
        end_headers, body = admin_account["headers"], {}
    for _ in range(2):
        finished = await client.post(end_url, headers=end_headers, json=body)
        assert finished.status_code == 200, finished.text
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == ("934.000000" if status == "sent" else "1000.000000")
    assert wallet["locked_balance"] == "0.000000"
    audit, transactions = await correction_records(item)
    assert len(audit) == len(transactions) == 1
    assert audit[0].admin_user_id == UUID(admin_account["id"])
    assert audit[0].old_data["held_total"] == "55.000000"
    assert audit[0].new_data["amount"] == "60.000000"
    assert audit[0].new_data["fee"] == "6.000000"
    assert audit[0].new_data["comment"] == adjustment_payload(item)["comment"]
    assert audit[0].new_data["wallet_transaction_id"] == str(transactions[0].id)
    assert transactions[0].available_delta_atomic == -11_000_000
    assert transactions[0].locked_delta_atomic == 11_000_000


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("amount", "fee", "available"),
    [("40.000000", "4.000000", "934.000000"), ("60.000000", "6.000000", "912.000000")],
)
async def test_completed_correction_uses_actual_debit_and_leaves_other_holds(
    client, make_account, admin_account, credit_balance, amount, fee, available
):
    user = await make_account()
    await credit_balance(user, "1000.000000")
    item = await create_withdrawal(client, user, "50")
    item = await advance_withdrawal(client, admin_account, item, "completed")
    assert item["held_total"] == "55.000000"
    assert item["final_total"] == "51.000000"  # 4 USDT уже вернулись при complete.
    await create_withdrawal(client, user)  # Отдельная заявка удерживает 22 USDT.
    response = await adjust(client, admin_account, item, amount, fee)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "completed"
    for _ in range(2):
        completed = await client.post(
            f"/api/v1/admin/withdrawals/{item['id']}/complete",
            headers=admin_account["headers"], json={},
        )
        assert completed.status_code == 200
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == available
    assert wallet["locked_balance"] == "22.000000"
    audit, transactions = await correction_records(item)
    assert len(audit) == len(transactions) == 1
    assert audit[0].old_data["final_total"] == "51.000000"
    assert transactions[0].locked_delta_atomic == 0


@pytest.mark.asyncio
async def test_decreasing_sent_correction_releases_the_full_old_hold_difference(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    item = await advance_withdrawal(client, admin_account, item, "sent")
    response = await adjust(client, admin_account, item, "40", "4")
    assert response.status_code == 200, response.text
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "56.000000"
    assert wallet["locked_balance"] == "44.000000"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["pending_review", "completed"])
async def test_insufficient_funds_roll_back_and_same_key_can_retry_after_topup(
    client, make_account, admin_account, credit_balance, status
):
    user = await make_account()
    await credit_balance(user, "55")
    item = await create_withdrawal(client, user, "50")
    item = await advance_withdrawal(client, admin_account, item, status, actual_fee="5")
    key = str(uuid4())
    response = await adjust(client, admin_account, item, key=key)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "insufficient_balance"
    persisted = await client.get(f"/api/v1/admin/withdrawals/{item['id']}", headers=admin_account["headers"])
    assert persisted.json() == {**item, "user_id": user["id"], "user_email": user["email"]}
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "0.000000"
    assert wallet["locked_balance"] == ("55.000000" if status == "pending_review" else "0.000000")
    assert await correction_records(item) == ([], [])
    await credit_balance(user, "11")
    retried = await adjust(client, admin_account, item, key=key)
    assert retried.status_code == 200, retried.text


@pytest.mark.asyncio
async def test_retry_is_idempotent_but_changed_payload_or_stale_version_is_rejected(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    key = str(uuid4())
    first = await adjust(client, admin_account, item, key=key)
    second = await adjust(client, admin_account, item, key=key)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    changed_payload = await adjust(client, admin_account, item, "61", "6", key=key)
    assert changed_payload.status_code == 409
    assert changed_payload.json()["error"]["code"] == "idempotency_key_conflict"
    stale = await adjust(client, admin_account, item, "70", "7")
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "withdrawal_changed"
    audit, transactions = await correction_records(item)
    assert len(audit) == len(transactions) == 1
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "34.000000"
    assert wallet["locked_balance"] == "66.000000"


@pytest.mark.asyncio
async def test_same_total_change_is_still_audited_and_versioned(
    client, make_account, admin_account, credit_balance
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    key = str(uuid4())
    first = await adjust(client, admin_account, item, "54", "1", key=key)
    retry = await adjust(client, admin_account, item, "54", "1", key=key)
    assert first.status_code == retry.status_code == 200
    assert first.json()["updated_at"] != item["updated_at"]
    audit, transactions = await correction_records(item)
    assert len(audit) == len(transactions) == 1
    assert transactions[0].available_delta_atomic == transactions[0].locked_delta_atomic == 0


@pytest.mark.asyncio
async def test_audit_failure_rolls_back_withdrawal_and_balance(
    client, make_account, admin_account, credit_balance, monkeypatch
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")

    async def unavailable_audit(*args, **kwargs):
        raise RuntimeError("Test audit write failure")

    monkeypatch.setattr(AuditService, "record", unavailable_audit)
    response = await adjust(client, admin_account, item)
    assert response.status_code == 500
    current = (await client.get(f"/api/v1/admin/withdrawals/{item['id']}", headers=admin_account["headers"])).json()
    assert current["amount"] == item["amount"]
    assert current["fee"] == item["fee"]
    assert current["updated_at"] == item["updated_at"]
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "45.000000"
    assert wallet["locked_balance"] == "55.000000"
    assert await correction_records(item) == ([], [])


@pytest.mark.asyncio
async def test_only_admin_can_change_another_users_withdrawal(
    client, make_account, admin_account, credit_balance
):
    owner = await make_account()
    another = await make_account()
    await credit_balance(owner)
    item = await create_withdrawal(client, owner, "50")
    url = f"/api/v1/admin/withdrawals/{item['id']}/amounts"
    for headers, status in [({}, 401), (owner["headers"], 403), (another["headers"], 403)]:
        response = await client.patch(
            url, headers={**headers, "Idempotency-Key": str(uuid4())}, json=adjustment_payload(item)
        )
        assert response.status_code == status, response.text
    assert await correction_records(item) == ([], [])
    changed = await adjust(client, admin_account, item)
    assert changed.status_code == 200, changed.text


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["cancelled", "rejected"])
async def test_refunded_withdrawals_cannot_be_edited(
    client, make_account, admin_account, credit_balance, status
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    if status == "cancelled":
        ended = await client.post(f"/api/v1/wallet/withdrawals/{item['id']}/cancel", headers=user["headers"])
    else:
        ended = await client.post(
            f"/api/v1/admin/withdrawals/{item['id']}/reject", headers=admin_account["headers"],
            json={"comment": "Отклонение для проверки"},
        )
    assert ended.status_code == 200, ended.text
    response = await adjust(client, admin_account, ended.json())
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "withdrawal_amounts_not_editable"
    assert await correction_records(item) == ([], [])
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "100.000000"
    assert wallet["locked_balance"] == "0.000000"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": "0"}, {"amount": "-1"}, {"fee": "-1"},
        {"amount": "30.0000001"}, {"fee": "1.0000001"}, {"comment": "   "},
        {"expected_updated_at": None},
    ],
)
async def test_invalid_correction_is_rejected_before_mutation(
    client, make_account, admin_account, credit_balance, overrides
):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    response = await client.patch(
        f"/api/v1/admin/withdrawals/{item['id']}/amounts",
        headers={**admin_account["headers"], "Idempotency-Key": str(uuid4())},
        json={**adjustment_payload(item), **overrides},
    )
    assert response.status_code == 422, response.text
    assert await correction_records(item) == ([], [])


@pytest.mark.asyncio
async def test_idempotency_header_is_required(client, make_account, admin_account, credit_balance):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    response = await client.patch(
        f"/api/v1/admin/withdrawals/{item['id']}/amounts", headers=admin_account["headers"],
        json=adjustment_payload(item),
    )
    assert response.status_code == 422
    assert await correction_records(item) == ([], [])


@pytest.mark.asyncio
async def test_money_lock_refreshes_preloaded_wallet_after_another_transaction(
    client, make_account, credit_balance
):
    """Деньги, поступившие между чтением ORM-объекта и блокировкой, сохраняются."""
    user = await make_account()
    await credit_balance(user)
    async with async_session_maker() as session:
        preloaded = await WalletService.get_wallet(session, UUID(user["id"]))
        assert preloaded.available_balance_atomic == 100_000_000
        await credit_balance(user, "25")  # Отдельная HTTP/DB-транзакция.
        await WalletService.apply_change(
            session,
            user_id=UUID(user["id"]),
            operation_type=WalletOperationType.WITHDRAWAL_HOLD,
            available_delta_atomic=-10_000_000,
            locked_delta_atomic=10_000_000,
            idempotency_key=f"test-preloaded-wallet:{uuid4()}",
        )
        await session.commit()
        assert preloaded.available_balance_atomic == 115_000_000
        assert preloaded.locked_balance_atomic == 10_000_000
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "115.000000"
    assert wallet["locked_balance"] == "10.000000"
