import sqlite3
import subprocess
from multiprocessing import Pool
from pathlib import Path
from sqlite3 import Connection
from typing import Annotated

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from rich.tree import Tree

import cagey
from cagey._internal.scripts import add_ms, add_nmr, add_turbidity

console = Console()


def main(
    data: Annotated[Path, typer.Argument(help="Folder holding the data.")],
    database: Annotated[Path, typer.Argument(help="Database file to create.")],
    mzmine: Annotated[
        Path, typer.Option(help="Path to MZmine version 3.4.")
    ] = Path("MZmine"),
) -> None:
    """Create a new database.

    Get help with [bright_magenta]cagey[/] [green]help[/] [blue]new[/].
    """
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
        cagey.queries.create_tables(connection)

        reactions_task = progress.add_task(
            "[green]Adding reactions",
            total=5,
            start=False,
        )
        ms_data = tuple(data.glob("ms/*.d"))
        ms_task = progress.add_task(
            "[green]Adding mass spectra",
            total=len(ms_data),
            start=False,
        )
        nmr_data = tuple(data.glob("nmr/**/title"))
        nmr_task = progress.add_task(
            "[green]Adding NMR",
            total=len(nmr_data),
            start=False,
        )
        turbidity_data = tuple(data.glob("turbidity/**/turbidity_data.json"))
        turbidity_task = progress.add_task(
            "[green]Adding turbidity",
            total=len(turbidity_data),
            start=False,
        )
        _add_reactions(
            connection,
            progress,
            reactions_task,
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


def help() -> None:  # noqa: A001
    """Get help on how to use [bright_magenta]cagey[/] [green]new[/]."""
    console.print(
        """[bold green underline]cagey new[/]

Create a new database with [bright_magenta]cagey[/] [green]new[/] \
[blue]DATA DATABASE[/].

[bright_magenta]cagey[/] will extract all \
your data in [blue]DATA[/] and create a new \
database file at [blue]DATABASE[/]. The [blue]DATA[/] folder should have \
the following structure:
"""
    )
    console.print(folder_structure())
    console.print(
        """
In other words, it will have three subfolders: \
[dodger_blue1]ms[/], [dodger_blue1]nmr[/] and [dodger_blue1]turbidity[/]. \
Each of these holds the relevant experimental data."""
    )


def folder_structure() -> Tree:
    data_tree = Tree(":open_file_folder: [blue]DATA[/]")
    ms = data_tree.add(":open_file_folder: [dodger_blue1]ms[/]")
    ms.add(
        ":open_file_folder: "
        "[pale_turquoise1]experiment[/]_[green_yellow]plate[/]_[plum1]formulation-number[/].d"
    ).add(":open_file_folder: AcqData").add("...")
    ms.add(
        ":open_file_folder: "
        "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]01[/].d"
    ).add(":open_file_folder: AcqData").add("...")
    ms.add("...")

    nmr = data_tree.add(":open_file_folder: [dodger_blue1]nmr[/]")
    nmr.add(":open_file_folder: ...").add(":open_file_folder: pdata").add(
        "..."
    ).add(
        Group(
            "📄 title",
            Panel.fit(
                "[pale_turquoise1]experiment[/]_[green_yellow]plate[/]_[plum1]formulation-number[/]",
                border_style="red",
            ),
        )
    )
    nmr.add(":open_file_folder: ...").add(":open_file_folder: pdata").add(
        "..."
    ).add(
        Group(
            "📄 title",
            Panel.fit(
                "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]19[/]",
                border_style="red",
            ),
        )
    )
    turbidity = data_tree.add(":open_file_folder: [dodger_blue1]turbidity[/]")
    turbidity.add(":open_file_folder: ...").add(
        Group(
            "📄 turbidity_data.json",
            Panel.fit(
                '{[red]"experiment"[/]: [yellow]"AB-02-005"[/], '
                '[red]"plate"[/]: [medium_purple2]1[/], '
                '[red]"formulation_number"[/]: [medium_purple2]4[/]}',
                border_style="red",
            ),
        )
    )
    return data_tree


def _add_reactions(
    connection: Connection,
    progress: Progress,
    task: TaskID,
) -> None:
    progress.start_task(task)
    cagey.reactions.add_precursors(connection, commit=False)
    progress.update(task, advance=1)
    cagey.reactions.add_ab_02_005_data(connection, commit=False)
    progress.update(task, advance=1)
    cagey.reactions.add_ab_02_007_data(connection, commit=False)
    progress.update(task, advance=1)
    cagey.reactions.add_ab_02_009_data(connection, commit=False)
    progress.update(task, advance=1)
    connection.commit()
    progress.update(task, advance=1)
