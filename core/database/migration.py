from __future__ import annotations

import asyncio
import logging

from psycopg.errors import InvalidCatalogName
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Base
from core.config import config

logger = logging.getLogger(__name__)
DEFAULT_DB_NAME = "postgres"


def _build_sync_url() -> URL:
    """Convert the configured async URL into a sync-compatible one."""
    url = make_url(str(config.SQLALCHEMY_DATABASE_URI))
    drivername = url.drivername
    if "+asyncpg" in drivername:
        drivername = drivername.replace("+asyncpg", "+psycopg")
    return url.set(drivername=drivername)


def _is_missing_database(error: OperationalError) -> bool:
    """Check whether the operational error indicates a missing database."""
    origin = getattr(error, "orig", None)
    if isinstance(origin, InvalidCatalogName):
        return True
    return "does not exist" in str(error).lower()


def ensure_database_exists() -> None:
    """Create the configured database if it does not already exist."""
    sync_url = _build_sync_url()
    database_name = sync_url.database
    if not database_name:
        raise RuntimeError("POSTGRES_DB must be set to create the database automatically")

    primary_engine = create_engine(sync_url)
    try:
        with primary_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except OperationalError as exc:
        if not _is_missing_database(exc):
            raise
        logger.info("Database %s not found. Creating it.", database_name)
    else:
        logger.debug("Database %s already exists.", database_name)
        return
    finally:
        primary_engine.dispose()

    admin_engine = create_engine(
        sync_url.set(database=DEFAULT_DB_NAME),
        isolation_level="AUTOCOMMIT",
    )
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            logger.info("Database %s created successfully.", database_name)
    finally:
        admin_engine.dispose()


async def run_schema_migrations() -> None:
    """Apply schema migrations by ensuring all models exist."""
    engine = create_async_engine(str(config.SQLALCHEMY_DATABASE_URI))
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("Database schema is up to date.")
    finally:
        await engine.dispose()


async def prepare_database() -> None:
    """Ensure the configured database exists and apply pending migrations."""
    await asyncio.to_thread(ensure_database_exists)
    await run_schema_migrations()
