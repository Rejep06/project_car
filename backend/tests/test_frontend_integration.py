"""Проверки публичной конфигурации и CORS для двух frontend-приложений."""

import pytest


@pytest.mark.asyncio
async def test_public_system_config_does_not_expose_secrets(client):
    response = await client.get("/api/v1/system/config")
    assert response.status_code == 200
    body = response.json()
    assert body["asset"] == "USDT"
    assert body["network"] == "TRON (TRC20)"
    assert body["deposit_invoice_ttl_minutes"] == 30
    assert body["deposit_amount_reservation_hours"] == 24
    serialized = str(body).lower()
    assert "secret" not in serialized
    assert "api_key" not in serialized
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


def test_unmatched_deposit_schema_exposes_real_binance_fields():
    """Админ-интерфейс получает внешний Binance ID и фактическое время депозита."""
    from app.main import app

    schema = app.openapi()["components"]["schemas"]["UnmatchedDepositRead"]["properties"]
    for field in (
        "binance_record_id",
        "binance_deposit_id",
        "coin",
        "binance_status",
        "deposit_time",
        "txid_already_used",
    ):
        assert field in schema
    assert schema["binance_deposit_id"]["type"] == "string"
