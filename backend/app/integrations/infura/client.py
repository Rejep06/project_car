"""Асинхронный Ethereum JSON-RPC клиент для Infura."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.enums import BlockchainDepositStatus
from app.integrations.infura.schemas import BlockchainTransferData
from app.schemas.common import validate_evm_address

TRANSFER_EVENT_TOPIC = (
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
)


def _hex_to_int(value: str | None, *, field: str) -> int:
    if not isinstance(value, str) or not value.startswith("0x"):
        raise AppError(
            "infura_invalid_response",
            f"Infura вернул некорректное поле {field}",
            status_code=502,
        )
    try:
        return int(value, 16)
    except ValueError as exc:
        raise AppError(
            "infura_invalid_response",
            f"Infura вернул некорректное поле {field}",
            status_code=502,
        ) from exc


def address_to_topic(address: str) -> str:
    normalized = validate_evm_address(address)
    return "0x" + "0" * 24 + normalized[2:]


def topic_to_address(topic: str | None) -> str | None:
    if not isinstance(topic, str) or not topic.startswith("0x") or len(topic) != 66:
        return None
    return "0x" + topic[-40:].lower()


class InfuraEthereumClient:
    """Минимальный read-only клиент без зависимости от web3.py."""

    def __init__(
        self,
        settings: Settings,
        *,
        provider_network: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.provider_network = provider_network.strip().lower()
        self._request_ids = itertools.count(1)
        self._owns_client = http_client is None
        endpoint = settings.infura_rpc_url.strip()
        if not endpoint:
            if not settings.infura_api_key.strip():
                raise AppError(
                    "infura_not_configured",
                    "Не задан INFURA_API_KEY или INFURA_RPC_URL",
                    status_code=503,
                )
            endpoint = (
                f"https://{self.provider_network}.infura.io/v3/"
                f"{settings.infura_api_key.strip()}"
            )
        headers = {"Content-Type": "application/json"}
        if settings.infura_jwt.strip():
            headers["Authorization"] = f"Bearer {settings.infura_jwt.strip()}"
        if http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=endpoint,
                headers=headers,
                timeout=settings.infura_request_timeout_seconds,
            )
        else:
            http_client.headers.update(headers)
            self.http_client = http_client

    async def close(self) -> None:
        if self._owns_client:
            await self.http_client.aclose()

    async def _rpc(self, method: str, params: list[Any]) -> Any:
        payload = {
            "jsonrpc": "2.0",
            "id": next(self._request_ids),
            "method": method,
            "params": params,
        }
        try:
            response = await self.http_client.post("", json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AppError(
                "infura_request_failed",
                "Не удалось получить данные Ethereum через Infura",
                status_code=502,
            ) from exc
        if not isinstance(body, dict):
            raise AppError(
                "infura_invalid_response",
                "Infura вернул неожиданный формат ответа",
                status_code=502,
            )
        if body.get("error") is not None:
            error = body.get("error")
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise AppError(
                "infura_rpc_error",
                f"Infura JSON-RPC: {message or 'неизвестная ошибка'}",
                status_code=502,
            )
        if "result" not in body:
            raise AppError(
                "infura_invalid_response",
                "В ответе Infura отсутствует result",
                status_code=502,
            )
        return body["result"]

    async def get_chain_id(self) -> int:
        return _hex_to_int(await self._rpc("eth_chainId", []), field="chainId")

    async def get_block_number(self) -> int:
        return _hex_to_int(await self._rpc("eth_blockNumber", []), field="blockNumber")

    async def get_block_timestamp(self, block_number: int) -> datetime:
        result = await self._rpc("eth_getBlockByNumber", [hex(block_number), False])
        if not isinstance(result, dict):
            raise AppError(
                "infura_block_not_found",
                f"Infura не вернул блок {block_number}",
                status_code=502,
            )
        timestamp = _hex_to_int(result.get("timestamp"), field="timestamp")
        return datetime.fromtimestamp(timestamp, tz=UTC)

    async def get_erc20_transfer_logs(
        self,
        *,
        contract_address: str,
        recipient_addresses: list[str],
        from_block: int,
        to_block: int,
    ) -> list[dict[str, Any]]:
        if not recipient_addresses or from_block > to_block:
            return []
        topics = [address_to_topic(item) for item in recipient_addresses]
        result = await self._rpc(
            "eth_getLogs",
            [
                {
                    "fromBlock": hex(from_block),
                    "toBlock": hex(to_block),
                    "address": validate_evm_address(contract_address),
                    "topics": [TRANSFER_EVENT_TOPIC, None, topics],
                }
            ],
        )
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise AppError(
                "infura_invalid_response",
                "Infura вернул некорректный список событий",
                status_code=502,
            )
        return result

    async def normalize_erc20_transfers(
        self,
        *,
        logs: list[dict[str, Any]],
        latest_block: int,
        asset: str,
        network: str,
        token_contract_address: str,
    ) -> list[BlockchainTransferData]:
        block_times: dict[int, datetime] = {}
        result: list[BlockchainTransferData] = []
        contract = validate_evm_address(token_contract_address)
        for raw in logs:
            if raw.get("removed") is True:
                continue
            topics = raw.get("topics")
            if not isinstance(topics, list) or len(topics) < 3:
                continue
            txid = str(raw.get("transactionHash") or "").lower()
            block_hash = str(raw.get("blockHash") or "").lower() or None
            try:
                block_number = _hex_to_int(raw.get("blockNumber"), field="blockNumber")
                log_index = _hex_to_int(raw.get("logIndex"), field="logIndex")
                amount_atomic = _hex_to_int(raw.get("data"), field="data")
            except AppError:
                continue
            recipient = topic_to_address(topics[2])
            sender = topic_to_address(topics[1])
            if recipient is None or not txid.startswith("0x") or len(txid) != 66:
                continue
            if block_number not in block_times:
                block_times[block_number] = await self.get_block_timestamp(block_number)
            confirmations = max(0, latest_block - block_number + 1)
            external_id = f"{network.lower()}:{txid}:{log_index}"
            result.append(
                BlockchainTransferData(
                    external_id=external_id,
                    txid=txid,
                    log_index=log_index,
                    block_number=block_number,
                    block_hash=block_hash,
                    from_address=sender,
                    address=recipient,
                    asset=asset.upper(),
                    network=network.upper(),
                    provider="infura",
                    token_contract_address=contract,
                    amount_atomic=amount_atomic,
                    status=BlockchainDepositStatus.SUCCESS,
                    confirmations=confirmations,
                    detected_at=block_times[block_number],
                    raw_data=raw,
                )
            )
        return result
