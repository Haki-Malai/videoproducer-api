import asyncio

import typer
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Role, User
from core.config import config

app = typer.Typer()


def get_async_engine() -> AsyncEngine:
    """Get the async engine for the database.

    :return: The async engine.
    """
    return create_async_engine(str(config.SQLALCHEMY_DATABASE_URI))


async def async_init():
    """Initialize the database."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Database initialized.")

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            try:
                admin = User(
                    username=config.ADMIN_USERNAME,
                    password=config.ADMIN_PASSWORD,
                    role=Role.ADMIN,
                )
                session.add(admin)
                await session.commit()
                print("Admin user created.")
            except IntegrityError:
                print("Admin user already exists.")


async def async_drop(tables: str):
    """Helper function to drop tables asynchronously.

    :param tables: Specify 'all' to drop all tables, or provide a specific table prefix.
    """
    engine = get_async_engine()
    async with engine.begin() as conn:
        if tables == "all":
            await conn.run_sync(Base.metadata.drop_all)
            print("All tables dropped")
        else:
            drop_script = text(
                """
                DO $$
                DECLARE
                    r RECORD;
                BEGIN
                    FOR r IN (SELECT tablename FROM pg_tables
                              WHERE schemaname = 'public' AND tablename LIKE :table_name)
                    LOOP
                        EXECUTE 'DROP TABLE ' || quote_ident(r.tablename) || ' CASCADE';
                    END LOOP;
                END $$;
            """
            )
            await conn.execute(drop_script, {"table_name": f"{tables}%"})
            print("Tables dropped successfully.")


async def async_view():
    """Helper function to view all tables asynchronously."""
    engine = get_async_engine()
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            )
        )
        tables = [row[0] for row in result]
        print("Tables in the database:")
        for table in tables:
            print(table)


@app.command()
def init():
    """Initialize the database."""
    asyncio.run(async_init())


@app.command()
def drop(tables: str = typer.Argument(None)):
    """Drop tables in the database asynchronously.

    :param tables: Specify 'all' to drop all tables, or provide a specific table prefix.
    """
    asyncio.run(async_drop(tables))


@app.command()
def view():
    """View all tables in the database."""
    asyncio.run(async_view())


if __name__ == "__main__":
    app()
