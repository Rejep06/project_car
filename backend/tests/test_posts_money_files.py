"""24–26. Публичность новостей, целочисленные деньги и ограничения файлов."""

from uuid import uuid4

import pytest
from sqlalchemy import Float

from app.db.base import Base
from app.utils.money import MAX_ATOMIC, MoneyFormatError, format_amount, parse_amount


@pytest.mark.asyncio
async def test_draft_post_is_not_public(client, admin_account):
    slug = f"draft-{uuid4().hex[:8]}"
    created = await client.post(
        "/api/v1/admin/posts",
        headers=admin_account["headers"],
        json={
            "title": "Черновик",
            "slug": slug,
            "excerpt": "Не публиковать",
            "content": "Содержимое черновика",
            "cover_image_url": None,
        },
    )
    assert created.status_code == 201, created.text
    public = await client.get(f"/api/v1/posts/{slug}")
    assert public.status_code == 404
    listing = await client.get("/api/v1/posts")
    assert listing.json()["total"] == 0


def test_money_values_do_not_use_float():
    assert parse_amount("100.347000") == 100_347_000
    assert format_amount(100_347_000) == "100.347000"
    assert parse_amount("9223372036854.775807") == MAX_ATOMIC
    with pytest.raises(MoneyFormatError):
        parse_amount("9223372036854.775808")
    money_columns = {
        "amount_atomic",
        "price_atomic",
        "reward_amount_atomic",
        "available_balance_atomic",
        "locked_balance_atomic",
        "fee_atomic",
        "total_debit_atomic",
    }
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if column.name in money_columns or column.name.endswith("_atomic"):
                assert not isinstance(column.type, Float), f"{table.name}.{column.name}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content", "mime", "expected_status"),
    [
        ("malware.txt", b"not allowed", "text/plain", 415),
        (
            "huge.png",
            b"\x89PNG\r\n\x1a\n" + b"x" * (5 * 1024 * 1024 + 1),
            "image/png",
            413,
        ),
    ],
)
async def test_forbidden_or_large_file_is_rejected(
    client, make_account, filename, content, mime, expected_status
):
    user = await make_account()
    ticket = (
        await client.post(
            "/api/v1/support/tickets",
            headers=user["headers"],
            json={
                "category": "other",
                "subject": "Проверка файла",
                "message": "Тест ограничений",
                "txid": None,
                "related_deposit_invoice_id": None,
            },
        )
    ).json()
    message_id = ticket["messages"][0]["id"]
    response = await client.post(
        f"/api/v1/support/messages/{message_id}/attachments",
        headers=user["headers"],
        files=[("files", (filename, content, mime))],
    )
    assert response.status_code == expected_status, response.text
