import base64
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, User
from core.factory.factory import get_session
from core.server import create_app


@pytest.fixture(scope="session")
def app() -> Generator[FastAPI, Any, None]:
    """Create a new FastAPI app"""
    app = create_app()

    yield app


@pytest_asyncio.fixture(scope="function")
async def client(
    app: FastAPI, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """Create a new FastAPI AsyncClient"""

    async def _get_session():
        return db_session

    app.dependency_overrides[get_session] = _get_session

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def user(db_session: AsyncSession) -> AsyncGenerator[User, None]:
    """Create a user in the database."""
    user = User(username="user", password="password", role=Role.USER)
    db_session.add(user)
    await db_session.commit()
    yield user


@pytest_asyncio.fixture
async def authenticated_client(
    client: AsyncClient, db_session: AsyncSession, role: Role
):
    """Create an authenticated client with a given role using Basic Authentication."""
    user = User(username=f"{role.name.lower()}_user", password="password", role=role)
    db_session.add(user)
    await db_session.commit()

    # Create Basic Auth header
    credentials = f"{user.username}:password"
    encoded_credentials = base64.b64encode(credentials.encode()).decode("utf-8")
    headers = {"Authorization": f"Basic {encoded_credentials}"}

    response = await client.post("/api/v1/tokens", headers=headers)
    access_token = response.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {access_token}"})
    yield client
