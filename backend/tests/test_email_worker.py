"""Проверки транзакционной email-очереди и lease от повторной отправки."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.db.enums import EmailOutboxStatus
from app.db.models import EmailOutbox
from app.db.session import async_session_maker
from app.utils.datetime import ensure_utc, utcnow
from app.workers.email_worker import claim_messages


@pytest.mark.asyncio
async def test_claimed_email_gets_lease_and_is_not_claimed_twice() -> None:
    async with async_session_maker() as session:
        item = EmailOutbox(
            recipient_email="queue@example.com",
            subject="Тест",
            text_body="Текст",
            html_body="<p>Текст</p>",
            status=EmailOutboxStatus.PENDING,
            attempt_count=0,
            available_at=utcnow(),
        )
        session.add(item)
        await session.commit()
        item_id = item.id

    claimed = await claim_messages(batch_size=10, max_attempts=8)
    assert claimed == [item_id]

    async with async_session_maker() as session:
        item = await session.scalar(select(EmailOutbox).where(EmailOutbox.id == item_id))
        assert item is not None
        assert item.status == EmailOutboxStatus.SENDING
        assert item.attempt_count == 1
        assert ensure_utc(item.available_at) > utcnow() + timedelta(minutes=4)

    assert await claim_messages(batch_size=10, max_attempts=8) == []
