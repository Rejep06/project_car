"""3–7. Покупка, идемпотентность и worker вознаграждений."""

from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.models import RewardPayout, WalletTransaction
from app.db.session import async_session_maker
from app.services.reward_service import RewardService
from app.utils.datetime import utcnow


@pytest.mark.asyncio
async def test_subscription_purchase(client, make_account, admin_account, create_plan, credit_balance):
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan()
    response = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**user["headers"], "Idempotency-Key": "purchase-1"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["plan_id"] == plan["id"]
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"


@pytest.mark.asyncio
async def test_insufficient_balance(client, make_account, admin_account, create_plan):
    user = await make_account()
    plan = await create_plan(price="50.000000")
    response = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**user["headers"], "Idempotency-Key": "purchase-no-money"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "insufficient_balance"


@pytest.mark.asyncio
async def test_purchase_idempotency(client, make_account, admin_account, create_plan, credit_balance):
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan()
    headers = {**user["headers"], "Idempotency-Key": "same-purchase-key"}
    first = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase", headers=headers
    )
    second = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase", headers=headers
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"
    async with async_session_maker() as session:
        transactions = list(
            (
                await session.scalars(
                    select(WalletTransaction).where(
                        WalletTransaction.idempotency_key == "same-purchase-key"
                    )
                )
            ).all()
        )
        assert len(transactions) == 1


@pytest.mark.asyncio
async def test_reward_schedule_created(client, make_account, admin_account, create_plan, credit_balance):
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan(
        reward_frequency="monthly",
        reward_duration_value=3,
        reward_duration_unit="month",
    )
    response = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**user["headers"], "Idempotency-Key": "monthly-schedule"},
    )
    assert response.status_code == 201, response.text
    detail = await client.get(
        f"/api/v1/subscriptions/{response.json()['id']}", headers=user["headers"]
    )
    payouts = detail.json()["reward_payouts"]
    assert len(payouts) == 3
    assert all(item["status"] == "pending" for item in payouts)


@pytest.mark.asyncio
async def test_reward_worker_does_not_duplicate(client, make_account, admin_account, create_plan, credit_balance):
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan(
        reward_amount="1.000000",
        reward_frequency="daily",
        reward_duration_value=1,
        reward_duration_unit="day",
    )
    purchase = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase",
        headers={**user["headers"], "Idempotency-Key": "reward-worker-purchase"},
    )
    subscription_id = purchase.json()["id"]
    async with async_session_maker() as session:
        payout = await session.scalar(
            select(RewardPayout).where(
                RewardPayout.user_subscription_id == UUID(subscription_id)
            )
        )
        payout.due_at = utcnow() - timedelta(seconds=1)
        await session.commit()

    first = await RewardService.process_batch(async_session_maker, batch_size=50)
    second = await RewardService.process_batch(async_session_maker, batch_size=50)
    assert first == 1
    assert second == 0
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "91.000000"


@pytest.mark.asyncio
async def test_purchase_key_cannot_be_reused_for_another_plan(
    client, make_account, admin_account, create_plan, credit_balance
):
    """Один ключ идемпотентности не может описывать две разные покупки."""
    user = await make_account()
    await credit_balance(user)
    first_plan = await create_plan(title="Первый тариф")
    second_plan = await create_plan(title="Второй тариф")
    headers = {**user["headers"], "Idempotency-Key": "shared-purchase-key"}

    first = await client.post(
        f"/api/v1/subscriptions/{first_plan['id']}/purchase", headers=headers
    )
    conflict = await client.post(
        f"/api/v1/subscriptions/{second_plan['id']}/purchase", headers=headers
    )

    assert first.status_code == 201, first.text
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "idempotency_key_conflict"
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"


@pytest.mark.asyncio
async def test_purchase_replay_survives_plan_deactivation(
    client, make_account, admin_account, create_plan, credit_balance
):
    """Повтор уже выполненного запроса возвращает исходную покупку без списания."""
    user = await make_account()
    await credit_balance(user)
    plan = await create_plan()
    headers = {**user["headers"], "Idempotency-Key": "replay-after-disable"}

    first = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase", headers=headers
    )
    deactivated = await client.post(
        f"/api/v1/admin/plans/{plan['id']}/deactivate",
        headers=admin_account["headers"],
    )
    replay = await client.post(
        f"/api/v1/subscriptions/{plan['id']}/purchase", headers=headers
    )

    assert first.status_code == 201, first.text
    assert deactivated.status_code == 200, deactivated.text
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == first.json()["id"]
    wallet = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet.json()["available_balance"] == "90.000000"
