"""Streamlined automated data analysis."""

from cagey import ms, nmr, queries, reactions, turbidity
from cagey._internal.types import (
    MassSpectrumId,
    MassSpectrumPeak,
    MassSpectrumTopologyAssignment,
    NmrPeak,
    NmrSpectrum,
    NmrSpectrumId,
    Precursor,
    Precursors,
    Reaction,
    ReactionKey,
    Row,
    TurbidState,
)

__all__ = [
    "ms",
    "nmr",
    "queries",
    "reactions",
    "turbidity",
    "MassSpectrumId",
    "MassSpectrumPeak",
    "MassSpectrumTopologyAssignment",
    "NmrPeak",
    "NmrSpectrum",
    "NmrSpectrumId",
    "Precursor",
    "Precursors",
    "Reaction",
    "ReactionKey",
    "Row",
    "TurbidState",
]
