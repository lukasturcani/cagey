from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

import cagey


def main(
    title_file: Annotated[
        Path, typer.Argument(help="Path to an NMR title file.")
    ],
) -> None:
    """Extract NMR peaks."""
    console = Console()
    spectrum = cagey.nmr.get_spectrum(title_file.parent)

    aldehyde_table = Table(title="Aldehyde Peaks", header_style="bold magenta")
    aldehyde_table.add_column("id", style="cyan")
    aldehyde_table.add_column("ppm", style="blue")
    aldehyde_table.add_column("amplitude", style="blue")
    for id_, peak in enumerate(spectrum.aldehyde_peaks):
        aldehyde_table.add_row(str(id_), str(peak.ppm), str(peak.amplitude))
    console.print(aldehyde_table)

    imine_table = Table(title="Imine Peaks", header_style="bold magenta")
    imine_table.add_column("id", style="cyan")
    imine_table.add_column("ppm", style="blue")
    imine_table.add_column("amplitude", style="blue")
    for id_, peak in enumerate(spectrum.imine_peaks):
        imine_table.add_row(str(id_), str(peak.ppm), str(peak.amplitude))
    console.print(imine_table)
