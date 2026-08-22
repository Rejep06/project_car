"""Проверки SMTP hostname и безопасной DNS-диагностики."""

import socket
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.services import email_service
from app.services.email_service import EmailService, SMTPDNSResolutionError


def test_smtp_host_is_normalized() -> None:
    settings = Settings(smtp_host="  SMTP-Relay.Brevo.Com.  ")
    assert settings.smtp_host == "smtp-relay.brevo.com"


@pytest.mark.parametrize(
    "value",
    [
        "https://smtp-relay.brevo.com",
        "smtp-relay.brevo.com:587",
        "smtp-relay.brevo.com/path",
    ],
)
def test_smtp_host_rejects_url_port_and_path(value: str) -> None:
    with pytest.raises(ValidationError):
        Settings(smtp_host=value)


def test_enabled_delivery_requires_smtp_settings() -> None:
    with pytest.raises(ValidationError, match="SMTP_HOST"):
        Settings(
            email_delivery_enabled=True,
            smtp_host="",
            smtp_from_email="mailer@example.com",
        )


def test_resolve_smtp_host_returns_unique_addresses(monkeypatch) -> None:
    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(
            email_delivery_enabled=True,
            smtp_host="smtp.example.com",
            smtp_port=587,
        ),
    )
    monkeypatch.setattr(
        email_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.10", 587)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.10", 587)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::10", 587, 0, 0)),
        ],
    )

    assert EmailService.resolve_smtp_host() == ("192.0.2.10", "2001:db8::10")


def test_resolve_smtp_host_has_clear_error(monkeypatch) -> None:
    monkeypatch.setattr(
        email_service,
        "get_settings",
        lambda: SimpleNamespace(
            email_delivery_enabled=True,
            smtp_host="smtp.example.com",
            smtp_port=587,
        ),
    )

    def fail(*args, **kwargs):
        raise socket.gaierror(-5, "No address associated with hostname")

    monkeypatch.setattr(email_service.socket, "getaddrinfo", fail)

    with pytest.raises(SMTPDNSResolutionError, match="SMTP_HOST='smtp.example.com'"):
        EmailService.resolve_smtp_host()
