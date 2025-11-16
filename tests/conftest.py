import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from core.config import config

TEST_DATABASE_URL = f"{str(config.SQLALCHEMY_DATABASE_URI)}-test"


@pytest.fixture(scope="session")
def event_loop(request: pytest.FixtureRequest) -> Generator:  # noqa: ARG001
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    async_engine = create_async_engine(TEST_DATABASE_URL)
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        pass

    await async_engine.dispose()
