"""Streamlined automated data analysis."""

from cagey import ms, nmr, notebook, reactions
from cagey._internal.tables import (
    MassSpecPeak,
    MassSpecTopologyAssignment,
    MassSpectrum,
    NmrAldehydePeak,
    NmrIminePeak,
    NmrSpectrum,
    Precursor,
    Reaction,
    add_tables,
)

__all__ = [
    "ms",
    "nmr",
    "reactions",
    "notebook",
    "add_tables",
    "MassSpecPeak",
    "MassSpecPeak",
    "MassSpecTopologyAssignment",
    "MassSpectrum",
    "NmrAldehydePeak",
    "NmrIminePeak",
    "NmrSpectrum",
    "Precursor",
    "Reaction",
]
