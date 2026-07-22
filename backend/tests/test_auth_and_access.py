"""1–2. Авторизация и разграничение ролей."""

import pytest


@pytest.mark.asyncio
async def test_registration_and_login(client):
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "Strong123!"},
    )
    assert registration.status_code == 201
    assert registration.json()["email"] == "new@example.com"

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "new@example.com", "password": "Strong123!"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert refresh.json()["refresh_token"] != login.json()["refresh_token"]


@pytest.mark.asyncio
async def test_regular_user_cannot_use_admin_api(client, make_account):
    account = await make_account("regular@example.com")
    response = await client.get("/api/v1/admin/users", headers=account["headers"])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_required"
