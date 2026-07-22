"""Периодический worker чтения Binance deposit history."""

import asyncio
import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.session import async_session_maker
from app.integrations.binance.client import BinanceReadOnlyClient
from app.services.deposit_service import DepositService
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)


async def run_deposit_cycle(
    *,
    client: BinanceReadOnlyClient,
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> int:
    """Выполняет один цикл; подходит для fake-клиента в тестах."""
    async with session_factory() as session:
        await DepositService.expire_invoices(session)
        await session.commit()

    start_time = utcnow() - timedelta(hours=settings.binance_lookback_hours)
    deposits = await client.get_deposit_history(start_time=start_time)
    processed = 0
    for data in sorted(deposits, key=lambda item: item.detected_at):
        if not DepositService.is_target_deposit(data, settings):
            continue
        async with session_factory() as session:
            _, credited = await DepositService.process_binance_deposit(
                session, data=data
            )
            if credited:
                processed += 1
    return processed


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    client = BinanceReadOnlyClient(settings)
    logger.info("Deposit worker запущен")
    while True:
        try:
            if settings.binance_enabled:
                processed = await run_deposit_cycle(
                    client=client,
                    session_factory=async_session_maker,
                    settings=settings,
                )
                if processed:
                    logger.info("Автоматически зачислено депозитов: %s", processed)
            else:
                logger.info("Binance-интеграция отключена через BINANCE_ENABLED=false")
        except Exception:
            logger.exception("Ошибка цикла deposit worker")
        await asyncio.sleep(settings.deposit_poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
