"""Дополнительная проверка нормализации Binance без сетевого запроса."""

from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.integrations.binance.client import BinanceReadOnlyClient


@pytest.mark.asyncio
async def test_binance_client_normalizes_status_and_network():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["X-MBX-APIKEY"] == "read-only-key"
        assert "signature=" in str(request.url)
        return httpx.Response(
            200,
            json=[
                {
                    "id": "42",
                    "amount": "12.345000",
                    "coin": "USDT",
                    "network": "TRX",
                    "status": 1,
                    "address": "T" + "A" * 33,
                    "txId": "a" * 64,
                    "insertTime": 1_700_000_000_000,
                }
            ],
        )

    settings = Settings(
        app_env="test",
        network="TRON",
        asset="USDT",
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test",
        binance_api_key="read-only-key",
        binance_api_secret="secret",
        binance_deposit_address="T" + "A" * 33,
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://api.binance.com"
    ) as http_client:
        client = BinanceReadOnlyClient(settings, http_client)
        items = await client.get_deposit_history(datetime.now(UTC))
    assert items[0].network == "TRON"
    assert items[0].status == "success"
    assert items[0].amount_atomic == 12_345_000
