import typer

from cli.database import app as database_app
from cli.shell import app as shell_app

app = typer.Typer()
app.add_typer(database_app, name="db")
app.add_typer(shell_app, name="shell")
app()
