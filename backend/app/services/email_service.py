"""Очередь и доставка системных писем через обычный SMTP."""

from __future__ import annotations

import asyncio
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
import logging
import smtplib
import socket
import ssl
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.enums import EmailOutboxStatus
from app.db.models import EmailOutbox

logger = logging.getLogger(__name__)


class SMTPDNSResolutionError(RuntimeError):
    """SMTP hostname не удалось разрешить через DNS."""


class EmailService:
    @staticmethod
    async def queue(
        session: AsyncSession,
        *,
        recipient_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> EmailOutbox:
        item = EmailOutbox(
            recipient_email=recipient_email.strip().lower(),
            subject=subject.strip(),
            text_body=text_body,
            html_body=html_body,
            status=EmailOutboxStatus.PENDING,
            attempt_count=0,
        )
        session.add(item)
        await session.flush()
        return item

    @classmethod
    async def queue_verification_email(
        cls,
        session: AsyncSession,
        *,
        recipient_email: str,
        token: str,
        is_email_change: bool = False,
    ) -> EmailOutbox:
        settings = get_settings()
        url = f"{settings.frontend_base_url}/verify-email?token={token}"
        heading = "Подтвердите новый email" if is_email_change else "Подтвердите email"
        intro = (
            "Вы запросили изменение адреса электронной почты."
            if is_email_change
            else "Вы создали аккаунт в Automotive Club."
        )
        subject = f"{heading} — {settings.smtp_from_name or settings.app_name}"
        text_body = (
            f"{intro}\n\n{heading}, перейдя по ссылке:\n{url}\n\n"
            f"Ссылка действует {settings.email_verification_ttl_hours} ч. "
            "Если запрос сделали не вы, просто проигнорируйте письмо."
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#161616;max-width:620px">
          <h1 style="font-size:24px">{escape(heading)}</h1>
          <p>{escape(intro)}</p>
          <p><a href="{escape(url)}" style="display:inline-block;padding:12px 20px;background:#111;color:#fff;text-decoration:none;border-radius:8px">{escape(heading)}</a></p>
          <p>Ссылка действует {settings.email_verification_ttl_hours} ч.</p>
          <p style="color:#666">Если запрос сделали не вы, просто проигнорируйте письмо.</p>
        </div>
        """.strip()
        return await cls.queue(
            session,
            recipient_email=recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    @classmethod
    async def queue_password_reset_email(
        cls,
        session: AsyncSession,
        *,
        recipient_email: str,
        token: str,
    ) -> EmailOutbox:
        settings = get_settings()
        url = f"{settings.frontend_base_url}/reset-password?token={token}"
        subject = f"Восстановление пароля — {settings.smtp_from_name or settings.app_name}"
        text_body = (
            "Для восстановления пароля перейдите по ссылке:\n"
            f"{url}\n\nСсылка действует {settings.password_reset_ttl_minutes} мин. "
            "Если запрос сделали не вы, ничего не предпринимайте."
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#161616;max-width:620px">
          <h1 style="font-size:24px">Восстановление пароля</h1>
          <p>Нажмите кнопку, чтобы установить новый пароль.</p>
          <p><a href="{escape(url)}" style="display:inline-block;padding:12px 20px;background:#111;color:#fff;text-decoration:none;border-radius:8px">Восстановить пароль</a></p>
          <p>Ссылка действует {settings.password_reset_ttl_minutes} мин.</p>
          <p style="color:#666">Если запрос сделали не вы, ничего не предпринимайте.</p>
        </div>
        """.strip()
        return await cls.queue(
            session,
            recipient_email=recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    @classmethod
    async def queue_password_changed_email(
        cls, session: AsyncSession, *, recipient_email: str
    ) -> EmailOutbox:
        settings = get_settings()
        subject = f"Пароль изменён — {settings.smtp_from_name or settings.app_name}"
        text_body = (
            "Пароль вашего аккаунта был изменён. Все ранее открытые сессии завершены. "
            "Если это сделали не вы, срочно обратитесь в поддержку."
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#161616;max-width:620px">
          <h1 style="font-size:24px">Пароль изменён</h1>
          <p>{escape(text_body)}</p>
        </div>
        """.strip()
        return await cls.queue(
            session,
            recipient_email=recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    @classmethod
    async def queue_lottery_win_email(
        cls,
        session: AsyncSession,
        *,
        recipient_email: str,
        lottery_title: str,
        prize_title: str,
        message: str,
        manager_contact: str | None,
    ) -> EmailOutbox:
        settings = get_settings()
        subject = f"Вы выиграли приз — {lottery_title}"
        contact_line = (
            f"\nКонтакт менеджера: {manager_contact}" if manager_contact else ""
        )
        text_body = (
            f"Поздравляем! Вы выиграли «{prize_title}» в лотерее «{lottery_title}».\n"
            f"{message}{contact_line}"
        )
        contact_html = (
            f"<p><strong>Контакт менеджера:</strong> {escape(manager_contact)}</p>"
            if manager_contact
            else ""
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#161616;max-width:620px">
          <h1 style="font-size:24px">Поздравляем с победой!</h1>
          <p>Вы выиграли <strong>{escape(prize_title)}</strong> в лотерее <strong>{escape(lottery_title)}</strong>.</p>
          <p>{escape(message)}</p>
          {contact_html}
          <p><a href="{escape(settings.frontend_base_url)}/account/lotteries">Открыть личный кабинет</a></p>
        </div>
        """.strip()
        return await cls.queue(
            session,
            recipient_email=recipient_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
        )

    @staticmethod
    def resolve_smtp_host() -> tuple[str, ...]:
        """Проверяет DNS отдельно от отправки и возвращает найденные IP-адреса."""
        settings = get_settings()
        if not settings.email_delivery_enabled:
            return ()
        try:
            records = socket.getaddrinfo(
                settings.smtp_host,
                settings.smtp_port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise SMTPDNSResolutionError(
                "Не удалось разрешить SMTP_HOST="
                f"{settings.smtp_host!r} через DNS: {exc}. "
                "Проверьте SMTP_HOST без https:// и :порта, затем DNS "
                "внутри контейнера email-worker."
            ) from exc

        addresses = tuple(
            sorted({record[4][0] for record in records if record[4]})
        )
        if not addresses:
            raise SMTPDNSResolutionError(
                f"DNS не вернул адреса для SMTP_HOST={settings.smtp_host!r}"
            )
        return addresses

    @staticmethod
    def _send_sync(item: EmailOutbox) -> None:
        settings = get_settings()
        if not settings.email_delivery_enabled:
            logger.warning(
                "EMAIL_DELIVERY_ENABLED=false: письмо %s для %s отмечено как тестовое",
                item.id,
                item.recipient_email,
            )
            return

        message = EmailMessage()
        message["Subject"] = item.subject
        message["From"] = formataddr(
            (settings.smtp_from_name, settings.smtp_from_email)
        )
        message["To"] = item.recipient_email
        message.set_content(item.text_body)
        message.add_alternative(item.html_body, subtype="html")

        try:
            if settings.smtp_use_ssl:
                with smtplib.SMTP_SSL(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=settings.smtp_timeout_seconds,
                    context=ssl.create_default_context(),
                ) as smtp:
                    if settings.smtp_username:
                        smtp.login(settings.smtp_username, settings.smtp_password)
                    smtp.send_message(message)
                return

            with smtplib.SMTP(
                settings.smtp_host,
                settings.smtp_port,
                timeout=settings.smtp_timeout_seconds,
            ) as smtp:
                smtp.ehlo()
                if settings.smtp_starttls:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        except socket.gaierror as exc:
            raise SMTPDNSResolutionError(
                "Не удалось разрешить SMTP_HOST="
                f"{settings.smtp_host!r} через DNS: {exc}"
            ) from exc

    @classmethod
    async def deliver(cls, item: EmailOutbox) -> None:
        await asyncio.to_thread(cls._send_sync, item)
