from pathlib import Path
from typing import Annotated

import typer
from rich import print
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.tree import Tree

console = Console()

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.callback()
def main() -> None:
    """A cage database tool.

    Run [bright_magenta]cagey[/] [blue]help[/] for an introduction.
    """
    return


@app.command()
def help() -> None:
    """Get help on how to use [bright_magenta]cagey[/]."""
    console.print(
        """
[bright_magenta]cagey[/] creates and manages a database of cage data so \
that you don't have to and can focus on data analysis.

[bold green underline]What it's for[/]

We collect a range of experimental and computational data about cages, \
including their precursors, mass spectra, NMR and so on. This data \
comes in a range of dissimilar formats and is located across a broad range \
of files. Not so good for doing data analysis! [bright_magenta]cagey[/] \
helps you to organise this data into a single database, so that you can \
easily share your data with other people, as all your data will be stored \
in a single file, and so that you can easily analyse your data, as it will \
be stored in a standardised and well documented format.

[bold green underline]How it works[/]

First your create a new database using the \
[bright_magenta]cagey[/] [green]new[/] command. This will create a new \
database file and populate it with the data in the folder you provide. \
The data in the folder should be organised in a standardised format, \
described in help of the [green]new[/] command, i.e. when you run \
[bright_magenta]cagey[/] [green]new[/] [blue]help[/]. Your database file \
will contain all the data in the folder, but in a standardised format, \
so that you can easily share it with other people and easily analyse it. \
The data in the database is easily extracted into data frames, so that \
you can work with polars, pandas, or any other data analysis library you \
like. I strongly reccomend using polars - \
https://docs.pola.rs/user-guide/getting-started - \
as it is much faster than pandas, and has more intuitive API.

The database you create is a standard SQLite database, meaning the data \
comes in the form of tables, and you can use SQL to query the data. \
You do not have to know SQL to use [bright_magenta]cagey[/], Python will be \
sufficient, but it is \
useful to know, as it will allow you to do more complex queries. If you \
would like to learn SQL, I reccomend the following tutorial - \
https://www.codecademy.com/learn/learn-sql - it takes about 5 hours to \
complete.

Once you have your database you will write your own Python scripts to \
read the data held by it and perform data analysis on it. You won't need \
to have [bright_magenta]cagey[/] installed to do this step! \
[bright_magenta]cagey[/] is just a command line tool to help you create and \
manage your database. The \
[bright_magenta]cagey[/] documentation - https://cagey.readthedocs.io \
- contains examples for writing your own Python data analysis scripts using \
the [bright_magenta]cagey[/] database.

[bold green underline]How to use it[/]

[bright_magenta]cagey[/] is a command line tool composed of several \
sub-commands."""
    )


def print_folder_structure() -> None:
    data_tree = Tree(":open_file_folder: data")
    ms = data_tree.add(":open_file_folder: ms")
    ms.add(
        escape(
            ":open_file_folder: "
            "[pale_turquoise1]experiment[/]_[green_yellow]plate[/]_[plum1]formulation-number[/].d"
        )
    ).add(":open_file_folder: AcqData").add("...")
    ms.add(
        escape(
            ":open_file_folder: "
            "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]01[/].d"
        )
    ).add(":open_file_folder: AcqData").add("...")
    ms.add("...")

    nmr = data_tree.add(":open_file_folder: nmr")
    nmr.add(":open_file_folder: ...").add(":open_file_folder: pdata").add(
        "..."
    ).add(
        Group(
            "📄 title",
            Panel.fit(
                escape(
                    "[pale_turquoise1]experiment[/]_[green_yellow]plate[/]_[plum1]formulation-number[/]"
                ),
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
                escape(
                    "[pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]19[/]"
                ),
                border_style="red",
            ),
        )
    )
    turbidity = data_tree.add(":open_file_folder: turbidity")
    turbidity.add(":open_file_folder: ...").add(
        Group(
            "📄 turbidity_data.json",
            Panel.fit(
                escape(
                    '{[red]"experiment"[/]: [yellow]"AB-02-005"[/], '
                    '[red]"plate"[/]: [medium_purple2]1[/], '
                    '[red]"formulation_number"[/]: [medium_purple2]4[/]}'
                ),
                border_style="red",
            ),
        )
    )

    print(data_tree)


@app.command(
    no_args_is_help=True,
    help="""Create a new database.

To create a new database you must provide a folder containing the data
in a standardised format. This folder should have structure of the
following form:

📂 data
├── 📂 ms
│   ├── 📂 [pale_turquoise1]experiment[/]_[green_yellow]plate[/]_\
[plum1]formulation-number[/].d
│   │   └── 📂 AcqData
│   │       └── ...
│   ├── 📂 [pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_[plum1]01[/].d
│   │   └── 📂 AcqData
│   │       └── ...
│   └── ...
├── 📂 nmr
│   ├── 📂 ...
│   │   └── 📂 pdata
│   │       └── ...
│   │           └── 📄 title
│   │               ╭─────────────────────────────────────╮
│   │               │ [pale_turquoise1]experiment[/]_[green_yellow]plate[/]\
_[plum1]formulation-number[/] │
│   │               ╰─────────────────────────────────────╯
│   └── 📂 ...
│       └── 📂 pdata
│           └── ...
│               └── 📄 title
│                   ╭─────────────────╮
│                   │ [pale_turquoise1]AB-02-005[/]_[green_yellow]01[/]_\
[plum1]19[/] │
│                   ╰─────────────────╯
└── 📂 turbidity
    └── 📂 ...
        └── 📄 turbidity_data.json
            ╭──────────────────────────────────────────────────────────────────╮
            │ {[red]"experiment"[/]: [yellow]"AB-02-005"[/], \
[red]"plate"[/]: [medium_purple2]1[/], \
[red]"formulation_number"[/]: [medium_purple2]4[/]} │
            ╰──────────────────────────────────────────────────────────────────╯

    """,
)
def new(
    data: Annotated[
        Path, typer.Argument(help="The data to store in the database.")
    ],
    database: Annotated[Path, typer.Argument(help="The new database file.")],
) -> None:
    return


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
