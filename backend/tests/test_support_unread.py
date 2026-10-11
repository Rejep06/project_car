"""Unread support replies, explicit receipts and conversation access boundaries."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
import sqlalchemy as sa


async def create_ticket(client, account, subject="Нужна помощь"):
    response = await client.post(
        "/api/v1/support/tickets",
        headers=account["headers"],
        json={"category": "other", "subject": subject, "message": "Первое сообщение"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def reply(client, account, ticket, *, admin=False, text="Новое сообщение"):
    prefix = "/api/v1/admin/support" if admin else "/api/v1/support"
    response = await client.post(
        f"{prefix}/tickets/{ticket['id']}/messages",
        headers=account["headers"],
        json={"message": text},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def unread_count(client, account, *, admin=False):
    prefix = "/api/v1/admin/support" if admin else "/api/v1/support"
    response = await client.get(f"{prefix}/unread-count", headers=account["headers"])
    assert response.status_code == 200, response.text
    return response.json()["unread_count"]


@pytest.mark.asyncio
async def test_support_counts_incoming_messages_without_reading_on_get(
    client, make_account, admin_account
):
    owner = await make_account()
    ticket = await create_ticket(client, owner)
    assert ticket["unread_count"] == 0
    assert await unread_count(client, owner) == 0
    assert await unread_count(client, admin_account, admin=True) == 1

    answer = await reply(client, admin_account, ticket, admin=True)
    assert answer["read_at"] is None
    for _ in range(2):
        detail = await client.get(
            f"/api/v1/support/tickets/{ticket['id']}", headers=owner["headers"]
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["unread_count"] == 1
        assert all(message["read_at"] is None for message in detail.json()["messages"])
    listing = await client.get("/api/v1/support/tickets", headers=owner["headers"])
    assert listing.json()["items"][0]["unread_count"] == 1
    admin_listing = await client.get(
        "/api/v1/admin/support/tickets", headers=admin_account["headers"]
    )
    assert admin_listing.json()["items"][0]["unread_count"] == 1

    # Sending a message does not silently acknowledge the other side's reply.
    await reply(client, owner, ticket)
    assert await unread_count(client, owner) == 1
    assert await unread_count(client, admin_account, admin=True) == 2


@pytest.mark.asyncio
async def test_support_read_acknowledges_only_seen_incoming_ids(
    client, make_account, admin_account
):
    owner = await make_account()
    first = await create_ticket(client, owner, "Первое обращение")
    second = await create_ticket(client, owner, "Второе обращение")
    seen = await reply(client, admin_account, first, admin=True, text="Виден пользователю")
    snapshot = await client.get(
        f"/api/v1/support/tickets/{first['id']}", headers=owner["headers"]
    )
    seen_ids = [item["id"] for item in snapshot.json()["messages"]]
    # This reply arrives after the loaded snapshot but before its read request.
    unseen = await reply(client, admin_account, first, admin=True, text="Пришёл позже")
    another_ticket_reply = await reply(client, admin_account, second, admin=True)
    assert await unread_count(client, owner) == 3

    read_url = f"/api/v1/support/tickets/{first['id']}/read"
    payload = {"message_ids": seen_ids + [another_ticket_reply["id"]]}
    marked = await client.post(read_url, headers=owner["headers"], json=payload)
    assert marked.status_code == 200, marked.text
    assert marked.json() == {"unread_count": 2}
    detail = (
        await client.get(
            f"/api/v1/support/tickets/{first['id']}", headers=owner["headers"]
        )
    ).json()
    receipts = {item["id"]: item["read_at"] for item in detail["messages"]}
    assert detail["unread_count"] == 1
    assert receipts[seen["id"]] is not None
    assert receipts[unseen["id"]] is None
    assert receipts[first["messages"][0]["id"]] is None  # Own outgoing message.
    other_detail = (
        await client.get(
            f"/api/v1/support/tickets/{second['id']}", headers=owner["headers"]
        )
    ).json()
    assert other_detail["unread_count"] == 1

    duplicate = await client.post(read_url, headers=owner["headers"], json=payload)
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json() == {"unread_count": 2}
    after_duplicate = (
        await client.get(
            f"/api/v1/support/tickets/{first['id']}", headers=owner["headers"]
        )
    ).json()
    assert next(
        item["read_at"] for item in after_duplicate["messages"] if item["id"] == seen["id"]
    ) == receipts[seen["id"]]
    assert await unread_count(client, admin_account, admin=True) == 2


@pytest.mark.asyncio
async def test_support_unread_access_and_receipts_are_user_specific(
    client, make_account, admin_account
):
    owner = await make_account()
    stranger = await make_account()
    owned_ticket = await create_ticket(client, owner)
    foreign_ticket = await create_ticket(client, stranger)
    owned_reply = await reply(client, admin_account, owned_ticket, admin=True)
    foreign_reply = await reply(client, admin_account, foreign_ticket, admin=True)
    assert await unread_count(client, owner) == 1
    assert await unread_count(client, stranger) == 1

    owned_read_url = f"/api/v1/support/tickets/{owned_ticket['id']}/read"
    forbidden = await client.post(
        owned_read_url,
        headers=stranger["headers"],
        json={"message_ids": [owned_reply["id"]]},
    )
    assert forbidden.status_code == 404
    foreign_ids = await client.post(
        owned_read_url,
        headers=owner["headers"],
        json={"message_ids": [foreign_reply["id"]]},
    )
    assert foreign_ids.status_code == 200, foreign_ids.text
    assert foreign_ids.json() == {"unread_count": 1}
    assert await unread_count(client, stranger) == 1

    no_auth_count = await client.get("/api/v1/support/unread-count")
    no_auth_read = await client.post(
        owned_read_url, json={"message_ids": [owned_reply["id"]]}
    )
    assert no_auth_count.status_code == no_auth_read.status_code == 401
    no_admin_count = await client.get(
        "/api/v1/admin/support/unread-count", headers=owner["headers"]
    )
    no_admin_read = await client.post(
        f"/api/v1/admin/support/tickets/{owned_ticket['id']}/read",
        headers=owner["headers"],
        json={"message_ids": [owned_ticket["messages"][0]["id"]]},
    )
    assert no_admin_count.status_code == no_admin_read.status_code == 403

    marked = await client.post(
        owned_read_url,
        headers=owner["headers"],
        json={"message_ids": [owned_reply["id"]]},
    )
    assert marked.json() == {"unread_count": 0}
    assert await unread_count(client, stranger) == 1


@pytest.mark.asyncio
async def test_admin_receipts_preserve_new_messages_and_customer_inbox(
    client, make_account, admin_account
):
    owner = await make_account()
    stranger = await make_account()
    owned_ticket = await create_ticket(client, owner)
    foreign_ticket = await create_ticket(client, stranger)
    answer = await reply(client, admin_account, owned_ticket, admin=True)
    detail = await client.get(
        f"/api/v1/admin/support/tickets/{owned_ticket['id']}",
        headers=admin_account["headers"],
    )
    assert detail.status_code == 200, detail.text
    assert detail.json()["unread_count"] == 1
    later_message = await reply(client, owner, owned_ticket)

    read = await client.post(
        f"/api/v1/admin/support/tickets/{owned_ticket['id']}/read",
        headers=admin_account["headers"],
        json={
            "message_ids": [
                owned_ticket["messages"][0]["id"],
                answer["id"],
                foreign_ticket["messages"][0]["id"],
            ]
        },
    )
    assert read.status_code == 200, read.text
    assert read.json() == {"unread_count": 2}
    assert await unread_count(client, owner) == 1
    assert await unread_count(client, stranger) == 0
    detail = (
        await client.get(
            f"/api/v1/admin/support/tickets/{owned_ticket['id']}",
            headers=admin_account["headers"],
        )
    ).json()
    assert detail["unread_count"] == 1
    receipts = {item["id"]: item["read_at"] for item in detail["messages"]}
    assert receipts[owned_ticket["messages"][0]["id"]] is not None
    assert receipts[later_message["id"]] is None
    assert receipts[answer["id"]] is None


def test_support_read_migration_preserves_history_and_leaves_new_messages_unread():
    migration_path = (
        Path(__file__).parents[1] / "alembic" / "versions" / "0007_support_message_reads.py"
    )
    spec = importlib.util.spec_from_file_location("support_read_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE support_messages (id INTEGER PRIMARY KEY, ticket_id INTEGER, "
            "message TEXT, created_at DATETIME NOT NULL)"
        )
        connection.exec_driver_sql(
            "INSERT INTO support_messages VALUES (1, 10, 'existing history', CURRENT_TIMESTAMP)"
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        old_receipt = connection.exec_driver_sql(
            "SELECT read_at FROM support_messages WHERE id = 1"
        ).scalar_one()
        assert old_receipt is not None
        connection.exec_driver_sql(
            "INSERT INTO support_messages (id, ticket_id, message, created_at) "
            "VALUES (2, 10, 'new reply', CURRENT_TIMESTAMP)"
        )
        assert connection.exec_driver_sql(
            "SELECT read_at FROM support_messages WHERE id = 2"
        ).scalar_one() is None
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert connection.exec_driver_sql(
            "SELECT message FROM support_messages ORDER BY id"
        ).scalars().all() == ["existing history", "new reply"]
    engine.dispose()
