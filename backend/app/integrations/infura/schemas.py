"""Нормализованные данные входящих переводов из блокчейн-провайдера."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.enums import BlockchainDepositStatus


class BlockchainTransferData(BaseModel):
    """Одно событие входящего перевода, готовое для бизнес-логики."""

    model_config = ConfigDict(frozen=True)

    external_id: str
    txid: str
    log_index: int
    block_number: int
    block_hash: str | None
    from_address: str | None
    address: str
    asset: str
    network: str
    provider: str
    token_contract_address: str | None
    amount_atomic: int
    status: BlockchainDepositStatus
    confirmations: int
    detected_at: datetime
    raw_data: dict[str, Any]
