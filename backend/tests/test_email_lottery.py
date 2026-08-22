"""Проверки покупки билетов, выбора победителей и выдачи призов."""

from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy import select

from app.db.models import Lottery
from app.db.session import async_session_maker
from app.utils.datetime import utcnow


async def create_lottery(client, admin, *, suffix: str, prize_type: str, amount: str | None = None):
    now = utcnow()
    response = await client.post(
        "/api/v1/admin/lotteries",
        headers=admin["headers"],
        json={
            "title": f"Лотерея {suffix}",
            "description": "Большая тестовая лотерея для проверки полного цикла.",
            "cover_image_url": None,
            "ticket_price": "5.000000",
            "sales_start_at": (now - timedelta(minutes=1)).isoformat(),
            "sales_end_at": (now + timedelta(hours=1)).isoformat(),
            "draw_at": (now + timedelta(hours=2)).isoformat(),
            "max_tickets_total": 100,
            "max_tickets_per_user": 10,
            "manager_telegram": "@automotive_manager",
            "rules_text": "Покупка билета подтверждает согласие участника с правилами розыгрыша.",
            "rules_version": "test-1",
        },
    )
    assert response.status_code == 201, response.text
    lottery = response.json()
    prize_payload = {
        "title": "Денежный приз" if prize_type == "balance" else "Автомобильный аксессуар",
        "description": "Приз победителю тестовой лотереи",
        "prize_type": prize_type,
        "amount": amount,
        "quantity": 1,
        "sort_order": 1,
        "image_url": None,
        "manager_telegram": "@automotive_manager",
    }
    prize = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/prizes",
        json=prize_payload,
        headers=admin["headers"],
    )
    assert prize.status_code == 201, prize.text
    published = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/publish",
        headers=admin["headers"],
    )
    assert published.status_code == 200, published.text
    return published.json(), prize.json()


async def make_draw_ready(lottery_id: str) -> None:
    async with async_session_maker() as session:
        item = await session.scalar(select(Lottery).where(Lottery.id == UUID(lottery_id)))
        assert item is not None
        item.sales_end_at = utcnow() - timedelta(minutes=2)
        item.draw_at = utcnow() - timedelta(minutes=1)
        await session.commit()


@pytest.mark.asyncio
async def test_random_lottery_balance_prize_is_credited(
    client, make_account, admin_account, credit_balance
):
    user = await make_account("lottery-balance@example.com")
    await credit_balance(user, "50.000000")
    lottery, _ = await create_lottery(
        client, admin_account, suffix="Баланс", prize_type="balance", amount="12.500000"
    )

    purchase = await client.post(
        f"/api/v1/lotteries/{lottery['id']}/tickets",
        json={"quantity": 2, "accept_rules": True},
        headers={**user["headers"], "Idempotency-Key": "lottery-test-balance"},
    )
    assert purchase.status_code == 201, purchase.text
    assert len(purchase.json()["tickets"]) == 2

    wallet_after_purchase = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet_after_purchase.json()["available_balance"] == "40.000000"

    await make_draw_ready(lottery["id"])
    draw = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/draw-random",
        headers=admin_account["headers"],
    )
    assert draw.status_code == 200, draw.text
    winner = draw.json()[0]
    assert winner["status"] == "pending"

    confirmed = await client.post(
        f"/api/v1/admin/lotteries/winners/{winner['id']}/confirm",
        json={"note": "Проверено администратором"},
        headers=admin_account["headers"],
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"

    wallet_after_prize = await client.get("/api/v1/wallet", headers=user["headers"])
    assert wallet_after_prize.json()["available_balance"] == "52.500000"

    notifications = await client.get("/api/v1/notifications", headers=user["headers"])
    assert notifications.status_code == 200, notifications.text
    assert notifications.json()["items"][0]["notification_type"] == "lottery_win"


@pytest.mark.asyncio
async def test_admin_can_select_physical_prize_winner_manually(
    client, make_account, admin_account, credit_balance
):
    user = await make_account("lottery-physical@example.com")
    await credit_balance(user, "20.000000")
    lottery, prize = await create_lottery(
        client, admin_account, suffix="Подарок", prize_type="physical"
    )
    purchase = await client.post(
        f"/api/v1/lotteries/{lottery['id']}/tickets",
        json={"quantity": 1, "accept_rules": True},
        headers={**user["headers"], "Idempotency-Key": "lottery-test-physical"},
    )
    assert purchase.status_code == 201, purchase.text
    ticket = purchase.json()["tickets"][0]
    await make_draw_ready(lottery["id"])

    selected = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/winners/manual",
        json={"prize_id": prize["id"], "ticket_id": ticket["id"]},
        headers=admin_account["headers"],
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["selection_method"] == "manual"

    before_confirmation = await client.get(
        "/api/v1/lotteries/me/tickets", headers=user["headers"]
    )
    assert before_confirmation.status_code == 200, before_confirmation.text
    assert before_confirmation.json()["items"][0]["winner_status"] is None
    assert before_confirmation.json()["items"][0]["prize_title"] is None

    confirmed = await client.post(
        f"/api/v1/admin/lotteries/winners/{selected.json()['id']}/confirm",
        json={"note": "Менеджер готов выдать приз"},
        headers=admin_account["headers"],
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["claim_contact"] == "@automotive_manager"

    tickets = await client.get("/api/v1/lotteries/me/tickets", headers=user["headers"])
    assert tickets.status_code == 200, tickets.text
    assert tickets.json()["items"][0]["prize_type"] == "physical"
    assert tickets.json()["items"][0]["claim_contact"] == "@automotive_manager"


@pytest.mark.asyncio
async def test_lottery_allows_non_protected_update_after_ticket_sale(
    client, make_account, admin_account, credit_balance
):
    user = await make_account("lottery-update@example.com")
    await credit_balance(user, "20.000000")
    lottery, _ = await create_lottery(
        client, admin_account, suffix="Изменение", prize_type="balance", amount="5.000000"
    )
    purchase = await client.post(
        f"/api/v1/lotteries/{lottery['id']}/tickets",
        json={"quantity": 1, "accept_rules": True},
        headers={**user["headers"], "Idempotency-Key": "lottery-update-ticket"},
    )
    assert purchase.status_code == 201, purchase.text

    payload = {
        "title": "Обновлённое название лотереи",
        "description": lottery["description"],
        "cover_image_url": lottery["cover_image_url"],
        "ticket_price": lottery["ticket_price"],
        "sales_start_at": lottery["sales_start_at"],
        "sales_end_at": lottery["sales_end_at"],
        "draw_at": lottery["draw_at"],
        "max_tickets_total": lottery["max_tickets_total"],
        "max_tickets_per_user": lottery["max_tickets_per_user"],
        "manager_telegram": "@new_manager",
        "rules_text": lottery["rules_text"],
        "rules_version": lottery["rules_version"],
    }
    updated = await client.patch(
        f"/api/v1/admin/lotteries/{lottery['id']}",
        json=payload,
        headers=admin_account["headers"],
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Обновлённое название лотереи"
    assert updated.json()["manager_telegram"] == "@new_manager"

    payload["ticket_price"] = "6.000000"
    rejected = await client.patch(
        f"/api/v1/admin/lotteries/{lottery['id']}",
        json=payload,
        headers=admin_account["headers"],
    )
    assert rejected.status_code == 409, rejected.text
    assert rejected.json()["error"]["code"] == "lottery_has_tickets"


@pytest.mark.asyncio
async def test_pending_manual_winner_can_be_removed_and_selected_again(
    client, make_account, admin_account, credit_balance
):
    user = await make_account("lottery-reselect@example.com")
    await credit_balance(user, "20.000000")
    lottery, prize = await create_lottery(
        client, admin_account, suffix="Перевыбор", prize_type="physical"
    )
    purchase = await client.post(
        f"/api/v1/lotteries/{lottery['id']}/tickets",
        json={"quantity": 1, "accept_rules": True},
        headers={**user["headers"], "Idempotency-Key": "lottery-reselect-ticket"},
    )
    ticket = purchase.json()["tickets"][0]
    await make_draw_ready(lottery["id"])

    first = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/winners/manual",
        json={"prize_id": prize["id"], "ticket_id": ticket["id"]},
        headers=admin_account["headers"],
    )
    assert first.status_code == 200, first.text
    removed = await client.delete(
        f"/api/v1/admin/lotteries/winners/{first.json()['id']}",
        headers=admin_account["headers"],
    )
    assert removed.status_code == 200, removed.text

    second = await client.post(
        f"/api/v1/admin/lotteries/{lottery['id']}/winners/manual",
        json={"prize_id": prize["id"], "ticket_id": ticket["id"]},
        headers=admin_account["headers"],
    )
    assert second.status_code == 200, second.text
    assert second.json()["id"] != first.json()["id"]


@pytest.mark.asyncio
async def test_admin_can_search_all_lottery_tickets(
    client, make_account, admin_account, credit_balance
):
    user = await make_account("lottery-search@example.com")
    await credit_balance(user, "20.000000")
    lottery, _ = await create_lottery(
        client, admin_account, suffix="Поиск", prize_type="balance", amount="5.000000"
    )
    purchase = await client.post(
        f"/api/v1/lotteries/{lottery['id']}/tickets",
        json={"quantity": 2, "accept_rules": True},
        headers={**user["headers"], "Idempotency-Key": "lottery-search-ticket"},
    )
    assert purchase.status_code == 201, purchase.text
    ticket_code = purchase.json()["tickets"][0]["ticket_code"]

    by_email = await client.get(
        f"/api/v1/admin/lotteries/{lottery['id']}/tickets",
        params={"page": 1, "page_size": 100, "search": "lottery-search@example.com"},
        headers=admin_account["headers"],
    )
    assert by_email.status_code == 200, by_email.text
    assert by_email.json()["total"] == 2

    by_code = await client.get(
        f"/api/v1/admin/lotteries/{lottery['id']}/tickets",
        params={"page": 1, "page_size": 100, "search": ticket_code},
        headers=admin_account["headers"],
    )
    assert by_code.status_code == 200, by_code.text
    assert by_code.json()["total"] == 1
    assert by_code.json()["items"][0]["ticket_code"] == ticket_code
