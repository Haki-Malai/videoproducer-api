import base64

import pytest
from httpx import AsyncClient
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from app.models import User


@pytest.mark.asyncio
class TestTokenEndpoints:
    async def test_login(self, client: AsyncClient, user: User):
        credentials = base64.b64encode(f"{user.username}:password".encode()).decode(
            "utf-8"
        )
        headers = {"Authorization": f"Basic {credentials}"}
        response = await client.post("/api/v1/tokens", headers=headers)
        assert response.status_code == 200

    async def test_refresh_token_success(self, client: AsyncClient, user: User):
        credentials = f"{user.username}:password"
        encoded_credentials = base64.b64encode(credentials.encode()).decode("utf-8")
        headers = {"Authorization": f"Basic {encoded_credentials}"}
        token_response = await client.post("/api/v1/tokens", headers=headers)

        refresh_token = token_response.json()["refresh_token"]
        access_token = token_response.json()["access_token"]

        client.headers.update({"Authorization": f"Bearer {access_token}"})

        refresh_response = await client.put(
            f"/api/v1/tokens?refresh_token={refresh_token}"
        )
        assert refresh_response.status_code == HTTP_200_OK
        assert "access_token" in refresh_response.json()

    async def test_refresh_token_unauthorized(self, client: AsyncClient):
        refresh_response = await client.put(
            "/api/v1/tokens", json={"refresh_token": "invalid_or_expired_refresh_token"}
        )
        assert refresh_response.status_code == HTTP_401_UNAUTHORIZED
