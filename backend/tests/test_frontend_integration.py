"""Проверки публичной конфигурации, CORS и схем для frontend-приложений."""

import pytest


@pytest.mark.asyncio
async def test_public_system_config_does_not_expose_secrets(client):
    response = await client.get("/api/v1/system/config")
    assert response.status_code == 200
    body = response.json()
    assert body["asset"] == "USDT"
    assert body["network"] == "Ethereum (ERC-20)"
    assert body["deposit_invoice_ttl_minutes"] == 30
    assert body["deposit_amount_reservation_hours"] == 24
    assert body["withdrawal_fee_percent"] == 10
    assert "withdrawal_fee" not in body
    serialized = str(body).lower()
    assert "secret" not in serialized
    assert "api_key" not in serialized
    assert "infura" not in serialized
    assert "database" not in serialized


@pytest.mark.asyncio
async def test_customer_frontend_origin_is_allowed(client):
    response = await client.options(
        "/api/v1/plans",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_admin_frontend_origin_is_allowed(client):
    response = await client.options(
        "/api/v1/admin/plans",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,idempotency-key",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3001"


def test_unmatched_deposit_schema_exposes_blockchain_event_fields():
    """Админ-интерфейс получает фактические поля события ERC-20."""
    from app.main import app

    schema = app.openapi()["components"]["schemas"]["UnmatchedDepositRead"]["properties"]
    for field in (
        "blockchain_record_id",
        "event_id",
        "txid",
        "log_index",
        "block_number",
        "asset",
        "provider",
        "deposit_status",
        "confirmations",
        "deposit_time",
        "txid_already_used",
    ):
        assert field in schema
    assert schema["event_id"]["type"] == "string"
