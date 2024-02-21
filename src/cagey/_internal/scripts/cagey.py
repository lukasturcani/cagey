from enum import StrEnum
from typing import assert_never

import typer
from rich.console import Console

from cagey._internal.scripts import cagey_insert, cagey_new, ms, nmr


class Topic(StrEnum):
    INTRO = "intro"
    NEW = "new"


console = Console()

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
)
app.command(no_args_is_help=True, name="new")(cagey_new.main)
app.command(no_args_is_help=True, name="insert")(cagey_insert.main)
app.add_typer(ms.app, name="ms")
app.command(no_args_is_help=True, name="nmr")(nmr.main)


@app.callback()
def main() -> None:
    """A cage database tool.

    Run [bright_magenta]cagey[/] [blue]help[/] \
[green]intro[/] for an introduction.
    """
    return


@app.command(no_args_is_help=True)
def help(topic: Topic) -> None:  # noqa: A001
    """Get help on how to use [bright_magenta]cagey[/]."""
    match topic:
        case Topic.NEW:
            cagey_new.help()
        case Topic.INTRO:
            print_help()
        case _ as unreachable:
            assert_never(unreachable)


def print_help() -> None:
    console.print(
        """
[bright_magenta]cagey[/] creates and manages a database of cage data so \
that you don't have to and can focus on data analysis.

[bold green underline]What it's for[/]

We collect a range of experimental and computational data about cages, \
including their precursors, mass spectra, NMR and so on. This data \
comes in a range of dissimilar formats and is located across a broad range \
of files. Not so good for doing data analysis! [bright_magenta]cagey[/] \
organises this data into a single database, allowing you to jump right \
into the analysis of your data, as it will be stored in a standardised \
and well documented format. You will also be able to share your data \
with other people, as all your data will be stored in a single file.

[bold green underline]How it works[/]

First your create a new database using the \
[bright_magenta]cagey[/] [green]new[/] command. This will create a new \
database file and populate it with the data in the folder you provide. \
The data in the folder should be organised in a standardised format, \
described in help of the [green]new[/] command, i.e. when you run \
[bright_magenta]cagey[/] [green]help[/] [blue]new[/]. Your database file \
will contain all the data in the folder, but in a standardised format. \
The data in the database can be extracted into data frames, so that \
you can work with polars, pandas, or any other data analysis library you \
like. I strongly reccomend using polars - \
https://docs.pola.rs/user-guide/getting-started - \
as it is much faster than pandas, and has more intuitive API. Worth it for \
even the seasoned pandas user!

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
sub-commands. You can see a list of these sub-commands by running \
[bright_magenta]cagey[/]. You can get help on how to use \
each sub-command by running \
[bright_magenta]cagey[/] [green]help[/] [blue]sub-command[/]. For example, \
to get help on how to use the [green]new[/] sub-command, you would run \
[bright_magenta]cagey[/] [green]help[/] [blue]new[/].

Normally you will use [bright_magenta]cagey[/] [green]new[/] to create a new \
database, and [bright_magenta]cagey[/] [green]insert[/] to insert new data \
into the database. That's pretty much it! Once you have your database you can \
write your own Python scripts to read the data held by it and perform data \
analysis on it. Look at https://cagey.readthedocs.io for examples of how to \
do this."""
    )


if __name__ == "__main__":
    app()
