from pathlib import Path
from typing import Annotated

import typer
from rich import print
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def main() -> None:
    """Create a new database.

    Get help with [bright_magenta]cagey[/] [green]new[/] [blue]help[/].
    """
    return


def help() -> None:  # noqa: A001
    """Get help on how to use [bright_magenta]cagey[/] [green]new[/]."""
    console.print()


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

    """Create a new database.

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

    """
