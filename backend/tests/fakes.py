"""Тестовый Infura-клиент: тесты никогда не обращаются в интернет."""

from datetime import datetime
from typing import Any

from app.core.config import USDT_ETHEREUM_CONTRACT
from app.db.enums import BlockchainDepositStatus
from app.integrations.infura.schemas import BlockchainTransferData


class FakeInfuraClient:
    """Минимальная подмена методов, которые использует deposit worker."""

    def __init__(
        self,
        transfers: list[BlockchainTransferData] | None = None,
        *,
        chain_id: int = 1,
        latest_block: int = 100,
    ) -> None:
        self.transfers = transfers or []
        self.chain_id = chain_id
        self.latest_block = latest_block
        self.log_calls = 0
        self.closed = False

    async def get_chain_id(self) -> int:
        return self.chain_id

    async def get_block_number(self) -> int:
        return self.latest_block

    async def get_erc20_transfer_logs(
        self,
        *,
        contract_address: str,
        recipient_addresses: list[str],
        from_block: int,
        to_block: int,
    ) -> list[dict[str, Any]]:
        self.log_calls += 1
        recipients = {item.lower() for item in recipient_addresses}
        contract = contract_address.lower()
        return [
            {"_transfer": transfer}
            for transfer in self.transfers
            if transfer.address.lower() in recipients
            and (transfer.token_contract_address or "").lower() == contract
            and from_block <= transfer.block_number <= to_block
        ]

    async def normalize_erc20_transfers(
        self,
        *,
        logs: list[dict[str, Any]],
        latest_block: int,
        asset: str,
        network: str,
        token_contract_address: str,
    ) -> list[BlockchainTransferData]:
        del latest_block, asset, network, token_contract_address
        return [item["_transfer"] for item in logs]

    async def close(self) -> None:
        self.closed = True


def make_deposit(
    *,
    external_id: str,
    txid: str,
    address: str,
    amount_atomic: int,
    detected_at: datetime,
    log_index: int = 0,
    block_number: int = 80,
    network: str = "ETHEREUM",
    asset: str = "USDT",
    provider: str = "infura",
    token_contract_address: str = USDT_ETHEREUM_CONTRACT,
    confirmations: int = 21,
    status: BlockchainDepositStatus = BlockchainDepositStatus.SUCCESS,
) -> BlockchainTransferData:
    normalized_txid = txid.lower()
    if not normalized_txid.startswith("0x"):
        normalized_txid = f"0x{normalized_txid}"
    normalized_address = address.lower()
    return BlockchainTransferData(
        external_id=external_id,
        txid=normalized_txid,
        log_index=log_index,
        block_number=block_number,
        block_hash="0x" + "f" * 64,
        from_address="0x" + "b" * 40,
        address=normalized_address,
        asset=asset,
        network=network,
        provider=provider,
        token_contract_address=token_contract_address.lower(),
        amount_atomic=amount_atomic,
        status=status,
        confirmations=confirmations,
        detected_at=detected_at,
        raw_data={
            "transactionHash": normalized_txid,
            "logIndex": hex(log_index),
            "blockNumber": hex(block_number),
            "address": token_contract_address.lower(),
            "data": hex(amount_atomic),
        },
    )
