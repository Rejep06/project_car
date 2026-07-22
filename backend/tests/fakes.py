"""Тестовый Binance-клиент: тесты никогда не обращаются в интернет."""

from datetime import datetime

from app.db.enums import BinanceDepositStatus
from app.integrations.binance.schemas import BinanceDepositData


class FakeBinanceClient:
    def __init__(self, deposits: list[BinanceDepositData] | None = None) -> None:
        self.deposits = deposits or []
        self.calls = 0

    async def get_deposit_history(
        self, start_time: datetime | None = None
    ) -> list[BinanceDepositData]:
        self.calls += 1
        return list(self.deposits)


def make_deposit(
    *,
    external_id: str,
    txid: str,
    address: str,
    amount_atomic: int,
    detected_at: datetime,
    network: str = "TRON",
    coin: str = "USDT",
    status: BinanceDepositStatus = BinanceDepositStatus.SUCCESS,
) -> BinanceDepositData:
    return BinanceDepositData(
        binance_deposit_id=external_id,
        txid=txid,
        address=address,
        coin=coin,
        network=network,
        amount_atomic=amount_atomic,
        status=status,
        detected_at=detected_at,
        raw_data={
            "id": external_id,
            "txId": txid,
            "address": address,
            "amount": str(amount_atomic),
        },
    )
