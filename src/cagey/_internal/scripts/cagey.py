from pathlib import Path
from typing import Annotated
from rich.tree import Tree
from rich.text import Text
from rich import print
from rich.console import Group
from rich.panel import Panel
from rich.syntax import Syntax

import typer

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def main() -> None:
    """A cage database tool.

    [bright_magenta]cagey[/] creates and manages a database of cage data so
    that you don't have to and can focus on data analysis.

    [bold green underline]What it's for[/]

    We collect a range of experimental and computational data about cages,
    including their precursors, mass spectra, NMR and so on. This data
    comes in a range of dissimilar formats and is located across a broad range
    of files. Not so good for doing data analysis! [bright_magenta]cagey[/]
    helps you to organise this data into a single database, so that you can
    easily share your data with other people, as all your data will be stored
    in a single file, and so that you can easily analyse your data, as it will
    be stored in a standardised and well documented format.

    [bold green underline]How it works[/]


    [bold green underline]How to use it[/]

    [birght_magenta]cagey[/] is a command line tool composed of several
    sub-commands.

    """


data_tree = Tree(":open_file_folder: data")
ms = data_tree.add(":open_file_folder: ms")
ms.add(
    ":open_file_folder: "
    "[pale_turquoise1]experiment[/]_[green_yellow]plate[/]_[plum1]formulation-number[/].d"
).add(":open_file_folder: AcqData").add("...")
ms.add(
    ":open_file_folder: "
    "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]01[/].d"
).add(":open_file_folder: AcqData").add("...")
ms.add(
    ":open_file_folder: "
    "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]02[/].d"
).add(":open_file_folder: AcqData").add("...")
ms.add("...")

nmr = data_tree.add(":open_file_folder: nmr")
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
nmr.add(":open_file_folder: ...").add(":open_file_folder: pdata").add(
    "..."
).add(
    Group(
        "📄 title",
        Panel.fit(
            "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]20[/]",
            border_style="red",
        ),
    )
)


turbidity = data_tree.add(":open_file_folder: turbidity")
turbidity.add(":open_file_folder: ...").add(
    Group(
        "📄 turbidity_data.json",
        Panel.fit(
            Syntax(
                '{\n\t"experiment": "AB-02-005",\n\t"plate": 1,\n\t'
                '"formulation_number": 4\n}',
                "json",
            ),
            border_style="red",
        ),
    )
)

print(data_tree)


@app.command(
    no_args_is_help=True,
    help="""
    Create a new database.

    To create a new database you must provide a folder containing the data
    in a standardised format. This folder should have structure of the
    following form:

    """,
)
def new(
    data: Annotated[
        Path, typer.Argument(help="The data to store in the database.")
    ],
    database: Annotated[Path, typer.Argument(help="The new database file.")],
) -> None:
    pass


@app.command(no_args_is_help=True)
def insert(
    data: Annotated[
        Path, typer.Argument(help="The data to store in the database.")
    ],
    database: Annotated[Path, typer.Argument(help="The database file.")],
) -> None:
    """Scan a folder for new data and insert it into the database."""


if __name__ == "__main__":
    app()
