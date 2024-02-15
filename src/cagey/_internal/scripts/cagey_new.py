from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console, Group
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def main(
    data: Annotated[Path, typer.Argument(help="Folder holding the data.")],
    database: Annotated[Path, typer.Argument(help="Database file to create.")],
) -> None:
    """Create a new database.

    Get help with [bright_magenta]cagey[/] [green]help[/] [blue]new[/].
    """
    return


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
