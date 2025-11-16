from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from core.config import Config
from core.database import migration


@pytest.fixture
def test_config() -> Config:
    return Config(
        SECRET_KEY="secret",
        POSTGRES_USER="skyflow",
        POSTGRES_PASSWORD="pass123",
        POSTGRES_HOST="db.example.com",
        POSTGRES_DB="videoproducer",
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD="adminpass",
    )


def _make_context(connection: MagicMock | None = None) -> MagicMock:
    context = MagicMock()
    context.__enter__.return_value = connection or MagicMock()
    return context


def test_ensure_database_exists_skips_creation_when_database_is_available(
    monkeypatch: pytest.MonkeyPatch, test_config: Config
):
    monkeypatch.setattr(migration, "config", test_config, raising=False)

    engine = MagicMock()
    connection = MagicMock()
    engine.connect.return_value = _make_context(connection)

    create_engine_mock = MagicMock(return_value=engine)
    monkeypatch.setattr(migration, "create_engine", create_engine_mock)

    migration.ensure_database_exists()

    connection.execute.assert_called_once()
    create_engine_mock.assert_called_once()
    engine.dispose.assert_called_once()


def test_ensure_database_exists_creates_missing_database(
    monkeypatch: pytest.MonkeyPatch, test_config: Config
):
    monkeypatch.setattr(migration, "config", test_config, raising=False)

    missing_error = OperationalError(
        "SELECT 1",
        {},
        Exception('database "videoproducer" does not exist'),
    )

    writer_engine = MagicMock()
    writer_context = _make_context()
    writer_context.__enter__.side_effect = missing_error
    writer_engine.connect.return_value = writer_context

    admin_engine = MagicMock()
    admin_connection = MagicMock()
    admin_engine.connect.return_value = _make_context(admin_connection)

    create_engine_mock = MagicMock(side_effect=[writer_engine, admin_engine])
    monkeypatch.setattr(migration, "create_engine", create_engine_mock)

    migration.ensure_database_exists()

    assert create_engine_mock.call_count == 2
    admin_connection.execute.assert_called_once()
    writer_engine.dispose.assert_called_once()
    admin_engine.dispose.assert_called_once()


@pytest.mark.asyncio
async def test_prepare_database_runs_creation_and_migrations(monkeypatch: pytest.MonkeyPatch):
    ensure = MagicMock()
    monkeypatch.setattr(migration, "ensure_database_exists", ensure)

    run_migrations = AsyncMock()
    monkeypatch.setattr(migration, "run_schema_migrations", run_migrations)

    async def fake_to_thread(func, *args, **kwargs):
        func(*args, **kwargs)

    monkeypatch.setattr(migration.asyncio, "to_thread", fake_to_thread)

    await migration.prepare_database()

    ensure.assert_called_once()
    run_migrations.assert_awaited_once()
