import sqlite3
import subprocess
from collections.abc import Iterator
from multiprocessing import Pool
from pathlib import Path
from sqlite3 import Connection
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import (
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TimeElapsedColumn,
)

from cagey import ReactionKey
from cagey._internal.scripts import add_ms, add_nmr, add_turbidity


def main(
    data: Annotated[Path, typer.Argument(help="Folder holding the data.")],
    database: Annotated[Path, typer.Argument(help="Database file to create.")],
    mzmine: Annotated[
        Path, typer.Option(help="Path to MZmine version 3.4.")
    ] = Path("MZmine"),
) -> None:
    """Insert new data into the [bright_magenta]cagey[/] database.

    Works just like the [bright_magenta]cagey[/] [green]new[/] but \
skips data from reaction reactions already in the database.
    """
    console = Console()
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
    with (
        Progress(
            SpinnerColumn(
                finished_text="[green]:heavy_check_mark:",
            ),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            MofNCompleteColumn(),
            transient=False,
        ) as progress,
        Pool() as pool,
    ):
        connection = sqlite3.connect(database, check_same_thread=False)
        existing_ms = set(_existing_ms(connection))
        ms_data = tuple(
            path
            for path in data.glob("ms/*.d")
            if ReactionKey.from_ms_path(path) not in existing_ms
        )
        ms_task = progress.add_task(
            "[green]Adding mass spectra",
            total=len(ms_data),
            start=False,
        )
        existing_nmr = set(_existing_nmr(connection))
        nmr_data = tuple(
            path
            for path in data.glob("nmr/**/title")
            if ReactionKey.from_title_file(path) not in existing_nmr
        )
        nmr_task = progress.add_task(
            "[green]Adding NMR",
            total=len(nmr_data),
            start=False,
        )
        existing_turbidity = set(_existing_turbidity(connection))
        turbidity_data = tuple(
            path
            for path in data.glob("turbidity/**/turbidity_data.json")
            if ReactionKey.from_json_file(path) not in existing_turbidity
        )
        turbidity_task = progress.add_task(
            "[green]Adding turbidity",
            total=len(turbidity_data),
            start=False,
        )
        add_ms.main(
            connection,
            ms_data,
            mzmine,
            progress,
            ms_task,
            pool,
        )
        add_nmr.main(
            connection,
            nmr_data,
            progress,
            nmr_task,
        )
        add_turbidity.main(
            connection,
            turbidity_data,
            progress,
            turbidity_task,
        )


def _existing_ms(connection: Connection) -> Iterator[ReactionKey]:
    cursor = connection.execute(
        """
        SELECT
            reactions.experiment,
            reactions.plate,
            reactions.formulation_number
        FROM
            mass_spectra
        LEFT JOIN
            reactions
            ON mass_spectra.reaction_id = reactions.id
        """
    )
    yield from (
        ReactionKey(experiment, plate, formulation_number)
        for experiment, plate, formulation_number in cursor
    )


def _existing_nmr(connection: Connection) -> Iterator[ReactionKey]:
    cursor = connection.execute(
        """
        SELECT
            reactions.experiment,
            reactions.plate,
            reactions.formulation_number
        FROM
            nmr_spectra
        LEFT JOIN
            reactions
            ON nmr_spectra.reaction_id = reactions.id
        """
    )
    yield from (
        ReactionKey(experiment, plate, formulation_number)
        for experiment, plate, formulation_number in cursor
    )


def _existing_turbidity(connection: Connection) -> Iterator[ReactionKey]:
    cursor = connection.execute(
        """
        SELECT
            reactions.experiment,
            reactions.plate,
            reactions.formulation_number
        FROM
            turbidity_measurements
        LEFT JOIN
            reactions
            ON turbidity_measurements.reaction_id = reactions.id
        """
    )
    yield from (
        ReactionKey(experiment, plate, formulation_number)
        for experiment, plate, formulation_number in cursor
    )
