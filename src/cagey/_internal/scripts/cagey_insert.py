import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from rich.prompt import Confirm
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

from cagey.tables import Reaction

console = Console()


def main(
    data: Annotated[Path, typer.Argument(help="Folder holding the data.")],
    database: Annotated[Path, typer.Argument(help="Database file to create.")],
    mzmine: Annotated[
        Path, typer.Option(help="Path to MZmine version 3.4.")
    ] = Path("MZmine"),
) -> None:
    has_docker = (
        subprocess.run(
            ["/usr/bin/docker", "ps"],  # noqa: S603
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )
    if not has_docker:
        console.print(
            "Docker is not running. Please install and start Docker and "
            "try again."
        )
        raise typer.Abort
    if database.exists():
        overwrite = Confirm.ask(
            f"Database file [yellow2]{database}[/] already exists. "
            "Overwrite it?",
            default=False,
        )
        if not overwrite:
            raise typer.Abort
        database.unlink()

    engine = create_engine(
        f"sqlite:///{database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with Session(engine) as session, Progress(
        SpinnerColumn(
            finished_text="[green]:heavy_check_mark:",
        ),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        transient=False,
    ) as progress:
        ms_data = tuple(
            path
            for path in data.glob("ms/*.d")
            if ReactionKey.from_ms_path(path) not in mass_spectra
        )
        ms_task = progress.add_task(
            "[green]Adding mass spectra",
            total=len(ms_data),
            start=False,
        )
        topology_assignment_task = progress.add_task(
            "[green]Assigning topologies",
            start=False,
        )
        nmr_data = tuple(
            path
            for path in data.glob("nmr/**/title")
            if ReactionKey.from_nmr_path(path) not in nmr_spectra
        )
        nmr_task = progress.add_task(
            "[green]Adding NMR",
            total=len(nmr_data),
            start=False,
        )
        turbidity_data = tuple(
            path
            for path in data.glob("turbidity/**/turbidity_data.json")
            if ReactionKey.from_turbidity_path(path) not in turbidities
        )
        turbidity_task = progress.add_task(
            "[green]Adding turbidity",
            start=False,
        )


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int
