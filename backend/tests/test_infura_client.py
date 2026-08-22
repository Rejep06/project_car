"""Проверка Ethereum JSON-RPC и нормализации события USDT ERC-20 без сети."""

import json
from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings, USDT_ETHEREUM_CONTRACT
from app.integrations.infura.client import (
    TRANSFER_EVENT_TOPIC,
    InfuraEthereumClient,
    address_to_topic,
)


@pytest.mark.asyncio
async def test_infura_client_reads_and_normalizes_usdt_transfer():
    recipient = "0x" + "a" * 40
    sender = "0x" + "b" * 40
    txid = "0x" + "c" * 64
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-jwt"
        body = json.loads(request.content)
        method = body["method"]
        calls.append(method)
        if method == "eth_chainId":
            result = "0x1"
        elif method == "eth_blockNumber":
            result = "0x64"
        elif method == "eth_getLogs":
            params = body["params"][0]
            assert params["address"] == USDT_ETHEREUM_CONTRACT
            assert params["topics"] == [
                TRANSFER_EVENT_TOPIC,
                None,
                [address_to_topic(recipient)],
            ]
            result = [
                {
                    "address": USDT_ETHEREUM_CONTRACT,
                    "topics": [
                        TRANSFER_EVENT_TOPIC,
                        address_to_topic(sender),
                        address_to_topic(recipient),
                    ],
                    "data": hex(12_345_000),
                    "blockNumber": "0x5a",
                    "transactionHash": txid,
                    "transactionIndex": "0x1",
                    "blockHash": "0x" + "d" * 64,
                    "logIndex": "0x2",
                    "removed": False,
                }
            ]
        elif method == "eth_getBlockByNumber":
            assert body["params"] == ["0x5a", False]
            result = {"timestamp": hex(1_700_000_000)}
        else:
            raise AssertionError(f"Неожиданный RPC-метод: {method}")
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": result})

    settings = Settings(
        app_env="test",
        database_url="sqlite+aiosqlite:///:memory:",
        jwt_secret="test",
        infura_api_key="test-key",
        infura_jwt="test-jwt",
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://mainnet.infura.io/v3/test-key/",
    ) as http_client:
        client = InfuraEthereumClient(
            settings,
            provider_network="mainnet",
            http_client=http_client,
        )
        assert await client.get_chain_id() == 1
        latest = await client.get_block_number()
        logs = await client.get_erc20_transfer_logs(
            contract_address=USDT_ETHEREUM_CONTRACT,
            recipient_addresses=[recipient],
            from_block=80,
            to_block=95,
        )
        transfers = await client.normalize_erc20_transfers(
            logs=logs,
            latest_block=latest,
            asset="USDT",
            network="ETHEREUM",
            token_contract_address=USDT_ETHEREUM_CONTRACT,
        )

    assert calls == [
        "eth_chainId",
        "eth_blockNumber",
        "eth_getLogs",
        "eth_getBlockByNumber",
    ]
    assert len(transfers) == 1
    transfer = transfers[0]
    assert transfer.txid == txid
    assert transfer.log_index == 2
    assert transfer.block_number == 90
    assert transfer.address == recipient
    assert transfer.from_address == sender
    assert transfer.amount_atomic == 12_345_000
    assert transfer.confirmations == 11
    assert transfer.detected_at == datetime.fromtimestamp(1_700_000_000, tz=UTC)
    assert transfer.provider == "infura"
    assert transfer.network == "ETHEREUM"
