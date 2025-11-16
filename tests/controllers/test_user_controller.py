from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.controllers import UserController
from core.exceptions import UnauthorizedException


class DummyUser:
    def __init__(self, *, user_id: int = 1, valid_password: bool = True):
        self.id = user_id
        self._is_valid = valid_password

    def verify_password(self, password: str) -> bool:  # pragma: no cover - trivial
        return self._is_valid


class DummyJWTHandler:
    def __init__(self):
        self.encoded_payloads: list[dict] = []
        self.decode_map: dict[str, dict] = {}

    def encode(self, payload: dict) -> str:
        stored = payload.copy()
        self.encoded_payloads.append(stored)
        return f"token-{len(self.encoded_payloads)}"

    def decode(self, token: str) -> dict:
        if token not in self.decode_map:
            raise UnauthorizedException("Invalid token")
        return self.decode_map[token]


@pytest.fixture
def controller_and_handler(monkeypatch):
    repository = SimpleNamespace()
    repository.get_by_username = AsyncMock()
    handler = DummyJWTHandler()
    monkeypatch.setattr("app.controllers.user.jwt_handler", handler)
    ctrl = UserController(user_repository=repository)
    return ctrl, handler


@pytest.mark.asyncio
async def test_login_returns_tokens_when_credentials_valid(controller_and_handler):
    controller, handler = controller_and_handler
    controller.user_repository.get_by_username = AsyncMock(
        return_value=DummyUser(user_id=42)
    )

    token = await controller.login("pilot", "secret")

    assert token.access_token.startswith("token-")
    assert handler.encoded_payloads[0]["user_id"] == 42
    assert token.refresh_token.startswith("token-")


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(controller_and_handler):
    controller, _ = controller_and_handler
    controller.user_repository.get_by_username = AsyncMock(return_value=None)

    with pytest.raises(UnauthorizedException):
        await controller.login("ghost", "bad")

    controller.user_repository.get_by_username = AsyncMock(
        return_value=DummyUser(valid_password=False)
    )

    with pytest.raises(UnauthorizedException):
        await controller.login("pilot", "wrong")


@pytest.mark.asyncio
async def test_refresh_token_generates_new_tokens(controller_and_handler):
    controller, handler = controller_and_handler
    handler.decode_map = {
        "refresh-token": {"sub": "refresh_token"},
        "access-token": {"user_id": 55},
    }

    tokens = await controller.refresh_token("access-token", "refresh-token")

    assert tokens.access_token.startswith("token-")
    assert tokens.refresh_token.startswith("token-")
    assert handler.encoded_payloads[-2]["user_id"] == 55
    assert handler.encoded_payloads[-1]["sub"] == "refresh_token"


@pytest.mark.asyncio
async def test_refresh_token_rejects_bad_payload(controller_and_handler):
    controller, handler = controller_and_handler
    handler.decode_map = {
        "refresh-token": {},
        "access-token": {"user_id": 5},
    }

    with pytest.raises(UnauthorizedException):
        await controller.refresh_token("access-token", "refresh-token")
