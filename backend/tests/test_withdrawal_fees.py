"""Процентная комиссия: точность, резерв и возврат средств."""

import pytest

from app.core.config import Settings
from app.utils.money import MAX_ATOMIC, format_amount, parse_amount, percentage_fee
from tests.test_withdrawals import ETHEREUM_ADDRESS, create_withdrawal


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        ("20.000000", "2.000000"),
        ("50.000000", "5.000000"),
        ("100.000000", "10.000000"),
        ("20.000004", "2.000000"),
        ("20.000005", "2.000001"),
        ("9223372036854.775807", "922337203685.477581"),
    ],
)
def test_fee_uses_ten_percent_with_half_up_rounding(amount, expected):
    assert format_amount(percentage_fee(parse_amount(amount), 10)) == expected


def test_legacy_fixed_fee_is_ignored(monkeypatch):
    monkeypatch.setenv("WITHDRAWAL_FEE", "999.000000")
    monkeypatch.delenv("WITHDRAWAL_FEE_PERCENT", raising=False)
    settings = Settings(_env_file=None)
    assert settings.withdrawal_fee_percent == 10
    assert "withdrawal_fee" not in settings.model_dump()


@pytest.mark.parametrize("percent", [-1, 101, 10.5])
def test_invalid_fee_percentage_is_rejected(percent):
    with pytest.raises(ValueError):
        Settings(_env_file=None, withdrawal_fee_percent=percent)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("amount", "fee", "held"),
    [
        ("50.000000", "5.000000", "55.000000"),
        ("100.000000", "10.000000", "110.000000"),
        ("20.000005", "2.000001", "22.000006"),
    ],
)
async def test_new_withdrawal_holds_amount_plus_percentage(
    client, make_account, credit_balance, amount, fee, held
):
    user = await make_account()
    await credit_balance(user, "1000.000000")
    item = await create_withdrawal(client, user, amount)
    assert item["amount"] == amount
    assert item["fee"] == fee
    assert item["held_total"] == item["final_total"] == held
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["locked_balance"] == held
    assert wallet["available_balance"] == format_amount(parse_amount("1000") - parse_amount(held))


@pytest.mark.asyncio
async def test_cancel_returns_percentage_fee_once(client, make_account, credit_balance):
    user = await make_account()
    await credit_balance(user)
    item = await create_withdrawal(client, user, "50")
    for _ in range(2):
        response = await client.post(
            f"/api/v1/wallet/withdrawals/{item['id']}/cancel", headers=user["headers"]
        )
        assert response.status_code == 200, response.text
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == "100.000000"
    assert wallet["locked_balance"] == "0.000000"


@pytest.mark.asyncio
async def test_amount_and_fee_overflow_is_rejected_before_debit(client, make_account):
    user = await make_account()
    response = await client.post(
        "/api/v1/wallet/withdrawals",
        headers=user["headers"],
        json={"destination_address": ETHEREUM_ADDRESS, "amount": format_amount(MAX_ATOMIC)},
    )
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "withdrawal_amount_too_large"
    wallet = (await client.get("/api/v1/wallet", headers=user["headers"])).json()
    assert wallet["available_balance"] == wallet["locked_balance"] == "0.000000"
