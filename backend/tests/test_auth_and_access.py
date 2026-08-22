"""Авторизация, подтверждение email и разграничение ролей."""

import pytest
from sqlalchemy import select

from app.db.models import LegalConsent
from app.db.session import async_session_maker


REGISTRATION_PAYLOAD = {
    "email": "new@example.com",
    "password": "Strong123!",
    "accept_terms": True,
    "accept_privacy_policy": True,
    "accept_personal_data_processing": True,
    "accept_program_rules": True,
    "confirm_age_18": True,
}


@pytest.mark.asyncio
async def test_registration_requires_legal_consents(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "consent@example.com", "password": "Strong123!"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_registration_email_verification_and_login(client):
    registration = await client.post(
        "/api/v1/auth/register", json=REGISTRATION_PAYLOAD
    )
    assert registration.status_code == 201, registration.text
    body = registration.json()
    assert body["email"] == "new@example.com"
    assert body["verification_required"] is True
    token = body["debug_verification_token"]
    assert token

    before_verification = await client.post(
        "/api/v1/auth/login",
        json={"email": "new@example.com", "password": "Strong123!"},
    )
    assert before_verification.status_code == 403
    assert before_verification.json()["error"]["code"] == "email_not_verified"

    verified = await client.post(
        "/api/v1/auth/email-verification/confirm", json={"token": token}
    )
    assert verified.status_code == 200, verified.text

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "new@example.com", "password": "Strong123!"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["token_type"] == "bearer"

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["refresh_token"] != login.json()["refresh_token"]

    async with async_session_maker() as session:
        consents = list(
            (
                await session.scalars(
                    select(LegalConsent).order_by(LegalConsent.document_type)
                )
            ).all()
        )
    assert len(consents) == 5
    assert {item.consent_group for item in consents} == {
        "contract",
        "privacy",
        "eligibility",
    }
    assert len({item.acceptance_batch_id for item in consents}) == 1
    assert None not in {item.acceptance_batch_id for item in consents}
    assert {item.account_email for item in consents} == {"new@example.com"}
    assert all(item.acceptance_form_version == "2026-08-10" for item in consents)
    assert all(item.document_url and item.acceptance_text for item in consents)


@pytest.mark.asyncio
async def test_forgot_password_changes_password_and_revokes_old_session(client, make_account):
    account = await make_account("reset@example.com", password="OldPass123!")
    requested = await client.post(
        "/api/v1/auth/password-reset/request", json={"email": account["email"]}
    )
    assert requested.status_code == 200, requested.text
    # В test/development токен возвращается в тексте только при отключённой доставке.
    token = requested.json()["message"].split("Тестовый токен: ", 1)[1]

    reset = await client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewPass123!"},
    )
    assert reset.status_code == 200, reset.text

    old_login = await client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": "OldPass123!"},
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={"email": account["email"], "password": "NewPass123!"},
    )
    assert new_login.status_code == 200, new_login.text

    old_refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": account["refresh_token"]}
    )
    assert old_refresh.status_code == 401


@pytest.mark.asyncio
async def test_regular_user_cannot_use_admin_api(client, make_account):
    account = await make_account("regular@example.com")
    response = await client.get("/api/v1/admin/users", headers=account["headers"])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_required"


@pytest.mark.asyncio
async def test_email_change_requires_confirmation_and_revokes_old_session(
    client, make_account
):
    from urllib.parse import parse_qs, urlparse

    from app.db.models import EmailOutbox

    account = await make_account("before-change@example.com")
    response = await client.patch(
        "/api/v1/users/me",
        json={"email": "after-change@example.com"},
        headers=account["headers"],
    )
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "before-change@example.com"
    assert response.json()["pending_email"] == "after-change@example.com"

    async with async_session_maker() as session:
        queued = await session.scalar(
            select(EmailOutbox)
            .where(EmailOutbox.recipient_email == "after-change@example.com")
            .order_by(EmailOutbox.created_at.desc())
        )
        assert queued is not None
        verification_url = next(
            line for line in queued.text_body.splitlines() if "verify-email?token=" in line
        )
        token = parse_qs(urlparse(verification_url).query)["token"][0]

    confirmed = await client.post(
        "/api/v1/auth/email-verification/confirm", json={"token": token}
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["email"] == "after-change@example.com"

    old_email_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "before-change@example.com", "password": account["password"]},
    )
    assert old_email_login.status_code == 401

    new_email_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "after-change@example.com", "password": account["password"]},
    )
    assert new_email_login.status_code == 200, new_email_login.text

    old_refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": account["refresh_token"]}
    )
    assert old_refresh.status_code == 401
