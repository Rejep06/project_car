"""Возвращает исчерпавшие попытки письма в email-очередь."""

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import update

from app.core.config import get_settings
from app.db.enums import EmailOutboxStatus
from app.db.models import EmailOutbox
from app.db.session import async_session_maker
from app.utils.datetime import utcnow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Повторно поставить неотправленные письма в очередь"
    )
    parser.add_argument(
        "--all-failed",
        action="store_true",
        help="сбросить все failed-письма, а не только исчерпавшие лимит",
    )
    return parser.parse_args()


async def requeue(*, all_failed: bool) -> int:
    settings = get_settings()
    conditions = [EmailOutbox.status == EmailOutboxStatus.FAILED]
    if not all_failed:
        conditions.append(
            EmailOutbox.attempt_count >= settings.email_worker_max_attempts
        )

    async with async_session_maker() as session:
        result = await session.execute(
            update(EmailOutbox)
            .where(*conditions)
            .values(
                status=EmailOutboxStatus.PENDING,
                attempt_count=0,
                available_at=utcnow(),
                sent_at=None,
                last_error=None,
            )
        )
        await session.commit()
        return int(result.rowcount or 0)


def main() -> None:
    args = parse_args()
    count = asyncio.run(requeue(all_failed=args.all_failed))
    print(f"Писем возвращено в очередь: {count}")


if __name__ == "__main__":
    main()
