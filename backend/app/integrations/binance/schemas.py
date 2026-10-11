"""Нормализованные данные Binance без бизнес-логики сопоставления."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.db.enums import BlockchainDepositStatus as BinanceDepositStatus
from app.utils.datetime import ensure_utc
from app.utils.money import parse_amount

BINANCE_DEPOSIT_STATUS_MAP: dict[int, BinanceDepositStatus] = {
    0: BinanceDepositStatus.PENDING,
    1: BinanceDepositStatus.SUCCESS,
    2: BinanceDepositStatus.REJECTED,
    6: BinanceDepositStatus.CREDITED_LOCKED,
    7: BinanceDepositStatus.WRONG_DEPOSIT,
    8: BinanceDepositStatus.WAITING_CONFIRMATION,
}


def normalize_binance_status(value: int | str | None) -> BinanceDepositStatus:
    """Преобразует числовой статус Binance в доменное перечисление."""
    try:
        return BINANCE_DEPOSIT_STATUS_MAP[int(value)]
    except (TypeError, ValueError, KeyError):
        return BinanceDepositStatus.UNKNOWN


def normalize_network(value: str | None) -> str:
    """Сводит обозначения TRX/TRON/TRC20 к внутреннему значению TRON."""
    normalized = (value or "").strip().upper()
    if normalized in {"TRX", "TRON", "TRC20", "TRON(TRC20)", "TRON (TRC20)"}:
        return "TRON"
    return normalized


class BinanceDepositData(BaseModel):
    """Нормализованная запись истории пополнений Binance."""

    model_config = ConfigDict(frozen=True)

    binance_deposit_id: str
    txid: str
    address: str
    coin: str
    network: str
    amount_atomic: int
    status: BinanceDepositStatus
    detected_at: datetime
    raw_data: dict[str, Any]

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "BinanceDepositData":
        txid = str(item.get("txId") or item.get("txid") or "").strip().lower()
        external_id = item.get("id") or item.get("tranId") or item.get("depositId")
        if external_id is None:
            external_id = f"{txid}:{item.get('insertTime', '')}:{item.get('amount', '')}"
        timestamp_ms = int(item.get("insertTime") or item.get("successTime") or 0)
        detected_at = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        return cls(
            binance_deposit_id=str(external_id),
            txid=txid,
            address=str(item.get("address") or "").strip(),
            coin=str(item.get("coin") or "").strip().upper(),
            network=normalize_network(item.get("network")),
            amount_atomic=parse_amount(str(item.get("amount") or "0")),
            status=normalize_binance_status(item.get("status")),
            detected_at=ensure_utc(detected_at),
            raw_data=dict(item),
        )
