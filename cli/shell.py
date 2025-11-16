import asyncio
import contextlib

import nest_asyncio
import typer
from IPython.terminal.embed import InteractiveShellEmbed
from sqlalchemy.sql.expression import select  # noqa: F401

from app.models import *  # noqa: F403
from core.database.session import (
    get_session,
    reset_session_context,
    set_session_context,
)

app = typer.Typer()


@contextlib.asynccontextmanager
async def async_get_session():
    async for session in get_session():
        yield session


async def start_shell():
    """Start the interactive shell."""

    banner = "Interactive database shell. 'session' is available."

    session_context_token = set_session_context("interactive_shell")

    async with async_get_session() as session:
        shell_vars = globals().copy()
        shell_vars.update(locals())

        nest_asyncio.apply()

        shell = InteractiveShellEmbed(banner1=banner, user_ns=shell_vars)
        shell()

    await session.close()
    reset_session_context(session_context_token)


@app.command()
def shell():
    """Launch an interactive shell with a database session."""
    asyncio.run(start_shell())


if __name__ == "__main__":
    app()
