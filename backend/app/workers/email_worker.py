"""Фоновая отправка писем из транзакционной очереди."""

import argparse
import asyncio
from datetime import timedelta
import logging
from uuid import UUID

from sqlalchemy import or_, select

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.enums import EmailOutboxStatus
from app.db.models import EmailOutbox
from app.db.session import async_session_maker
from app.services.email_service import EmailService, SMTPDNSResolutionError
from app.utils.datetime import utcnow

logger = logging.getLogger(__name__)


async def claim_messages(batch_size: int, max_attempts: int) -> list[UUID]:
    async with async_session_maker() as session:
        items = list(
            (
                await session.scalars(
                    select(EmailOutbox)
                    .where(
                        EmailOutbox.available_at <= utcnow(),
                        EmailOutbox.attempt_count < max_attempts,
                        or_(
                            EmailOutbox.status == EmailOutboxStatus.PENDING,
                            EmailOutbox.status == EmailOutboxStatus.FAILED,
                            EmailOutbox.status == EmailOutboxStatus.SENDING,
                        ),
                    )
                    .order_by(EmailOutbox.created_at)
                    .with_for_update(of=EmailOutbox, skip_locked=True)
                    .limit(batch_size)
                )
            ).all()
        )
        lease_until = utcnow() + timedelta(minutes=5)
        for item in items:
            item.status = EmailOutboxStatus.SENDING
            item.attempt_count += 1
            item.last_error = None
            # Пока письмо отправляется, другой worker не должен забрать его
            # повторно. После истечения lease зависшее сообщение можно вернуть
            # в обработку автоматически.
            item.available_at = lease_until
        await session.commit()
        return [item.id for item in items]


async def process_message(message_id: UUID) -> bool:
    async with async_session_maker() as session:
        item = await session.scalar(
            select(EmailOutbox)
            .where(EmailOutbox.id == message_id)
            .with_for_update(of=EmailOutbox)
        )
        if item is None or item.status != EmailOutboxStatus.SENDING:
            return False
        try:
            await EmailService.deliver(item)
        except SMTPDNSResolutionError as exc:
            # DNS мог пропасть между предварительной проверкой и отправкой.
            # Такой инфраструктурный сбой не должен расходовать попытку письма.
            item.status = EmailOutboxStatus.PENDING
            item.attempt_count = max(0, item.attempt_count - 1)
            item.last_error = str(exc)[:4000]
            item.available_at = utcnow() + timedelta(
                seconds=get_settings().email_worker_interval_seconds
            )
            await session.commit()
            logger.warning(
                "Письмо %s возвращено в очередь: SMTP DNS недоступен",
                item.id,
            )
            return False
        except Exception as exc:  # noqa: BLE001 - worker должен переживать SMTP-сбои
            delay_seconds = min(3600, 2 ** min(item.attempt_count, 10) * 15)
            item.status = EmailOutboxStatus.FAILED
            item.last_error = str(exc)[:4000]
            item.available_at = utcnow() + timedelta(seconds=delay_seconds)
            await session.commit()
            logger.exception("Не удалось отправить письмо %s", item.id)
            return False

        item.status = EmailOutboxStatus.SENT
        item.sent_at = utcnow()
        item.last_error = None
        # Одноразовые ссылки больше не должны храниться в открытом виде.
        item.text_body = ""
        item.html_body = ""
        await session.commit()
        return True


async def process_batch() -> int:
    settings = get_settings()
    ids = await claim_messages(
        settings.email_worker_batch_size, settings.email_worker_max_attempts
    )
    processed = 0
    for message_id in ids:
        if await process_message(message_id):
            processed += 1
    return processed


async def smtp_dns_ready() -> tuple[str, ...]:
    """Не даёт очереди расходовать попытки, пока SMTP hostname не резолвится."""
    settings = get_settings()
    if not settings.email_delivery_enabled:
        return ()
    return await asyncio.to_thread(EmailService.resolve_smtp_host)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Обработчик email-очереди запущен")

    dns_failed = False
    while True:
        try:
            addresses = await smtp_dns_ready()
        except SMTPDNSResolutionError as exc:
            if not dns_failed:
                logger.error(
                    "SMTP DNS недоступен; очередь временно приостановлена: %s",
                    exc,
                )
            dns_failed = True
            await asyncio.sleep(settings.email_worker_interval_seconds)
            continue

        if dns_failed:
            logger.info("SMTP DNS снова доступен; обработка очереди продолжена")
        elif addresses:
            logger.debug(
                "SMTP DNS проверен: %s адрес(ов) для %s",
                len(addresses),
                settings.smtp_host,
            )
        dns_failed = False

        try:
            processed = await process_batch()
            if processed:
                logger.info("Отправлено писем: %s", processed)
        except Exception:  # noqa: BLE001
            logger.exception("Ошибка цикла email worker")
        await asyncio.sleep(settings.email_worker_interval_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Email worker")
    parser.add_argument(
        "--check",
        action="store_true",
        help="проверить конфигурацию и DNS SMTP, затем завершиться",
    )
    return parser.parse_args()


def run_check() -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    if not settings.email_delivery_enabled:
        print("EMAIL_DELIVERY_ENABLED=false: SMTP-проверка не требуется")
        return 0
    try:
        addresses = EmailService.resolve_smtp_host()
    except SMTPDNSResolutionError as exc:
        print(f"SMTP DNS ERROR: {exc}")
        return 1
    print(
        f"SMTP DNS OK: {settings.smtp_host}:{settings.smtp_port} -> "
        + ", ".join(addresses)
    )
    return 0


if __name__ == "__main__":
    args = parse_args()
    if args.check:
        raise SystemExit(run_check())
    asyncio.run(main())
