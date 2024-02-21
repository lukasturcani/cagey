import sqlite3
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

import cagey
from cagey.queries import Precursors, ReactionKey, Row

app = typer.Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@app.command(no_args_is_help=True)
def from_machine_data(  # noqa: PLR0913
    database: Path,
    machine_data: Path,
    mzmine: Annotated[
        Path, typer.Option(help="Path to MZmine version 3.4.")
    ] = Path("MZmine"),
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> None:
    """Perform analysis on a mass spectra from raw machine data.

    This command will not add the results to the database, but will \
instead print the results to the console.
    """
    console = Console()

    reaction_key = ReactionKey.from_ms_path(machine_data)
    connection = sqlite3.connect(database)
    ((_, precursors),) = cagey.queries.reaction_precursors(
        connection, [reaction_key]
    )
    mzml = cagey.ms.machine_data_to_mzml(machine_data)
    csv = cagey.ms.mzml_to_csv(mzml, mzmine)

    console.print(
        _get_table(
            csv=csv,
            precursors=precursors,
            calculated_peak_tolerance=calculated_peak_tolerance,
            separation_peak_tolerance=separation_peak_tolerance,
            max_ppm_error=max_ppm_error,
            max_separation=max_separation,
            min_peak_height=min_peak_height,
        )
    )


@app.command(no_args_is_help=True)
def from_csv(  # noqa: PLR0913
    database: Path,
    csv: Path,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> None:
    """Perform analysis on a mass spectra from a csv file.

    This command will not add the results to the database, but will \
instead print the results to the console.
    """
    console = Console()
    reaction_key = ReactionKey.from_ms_path(machine_data)
    connection = sqlite3.connect(database)
    ((_, precursors),) = cagey.queries.reaction_precursors(
        connection, [reaction_key]
    )
    console.print(
        _get_table(
            csv=csv,
            precursors=precursors,
            calculated_peak_tolerance=calculated_peak_tolerance,
            separation_peak_tolerance=separation_peak_tolerance,
            max_ppm_error=max_ppm_error,
            max_separation=max_separation,
            min_peak_height=min_peak_height,
        )
    )


def _get_table(  # noqa: PLR0913
    csv: Path,
    precursors: Precursors,
    *,
    calculated_peak_tolerance: float,
    separation_peak_tolerance: float,
    max_ppm_error: float,
    max_separation: float,
    min_peak_height: float,
) -> Table:
    table = Table(title="Mass Spectrum Peaks")
    table.add_column("id")
    table.add_column("di_count")
    table.add_column("tri_count")
    table.add_column("adduct")
    table.add_column("charge")
    table.add_column("calculated_mz")
    table.add_column("spectrum_mz")
    table.add_column("separation_mz")
    table.add_column("intensity")
    table.add_column("topology")

    rows = tuple(
        Row(id=id_, item=peak)
        for id_, peak in enumerate(
            cagey.ms.get_peaks(
                path=csv,
                di_smiles=precursors.di_smiles,
                tri_smiles=precursors.tri_smiles,
                calculated_peak_tolerance=calculated_peak_tolerance,
                separation_peak_tolerance=separation_peak_tolerance,
                max_ppm_error=max_ppm_error,
                max_separation=max_separation,
                min_peak_height=min_peak_height,
            )
        )
    )
    topologies = {
        assignment.mass_spectrum_peak_id: assignment.topology
        for assignment in cagey.ms.get_topologies(rows)
    }
    for row in rows:
        table.add_row(
            str(row.id),
            str(row.item.di_count),
            str(row.item.tri_count),
            str(row.item.adduct),
            str(row.item.charge),
            str(row.item.calculated_mz),
            str(row.item.spectrum_mz),
            str(row.item.separation_mz),
            str(row.item.intensity),
            topologies.get(row.id),
        )
    return table
