"""Периодический worker начисления просроченных reward payout."""

import asyncio
import logging

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import async_session_maker
from app.services.reward_service import RewardService

logger = logging.getLogger(__name__)


async def run_reward_cycle() -> int:
    settings = get_settings()
    return await RewardService.process_batch(
        async_session_maker,
        batch_size=settings.reward_worker_batch_size,
    )


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Reward worker запущен")
    while True:
        try:
            processed = await run_reward_cycle()
            if processed:
                logger.info("Начислено reward payout: %s", processed)
        except Exception:
            logger.exception("Ошибка цикла reward worker")
        await asyncio.sleep(settings.reward_worker_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
