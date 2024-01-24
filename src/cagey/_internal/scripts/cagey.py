import typer
from pathlib import Path

app = typer.Typer()

@app.callback()
def main() -> None:
    """Manages cage data.


    """


@app.command()
def new(database: Path, data: Path) -> None:
    """Create a new database."""


if __name__ == "__main__":
    app()
