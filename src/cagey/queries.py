"""Database tables."""

from cagey._internal.queries import (
    MassSpectrumPeak,
    insert_mass_spectrum,
)

__all__ = [
    "MassSpectrumPeak",
    "insert_mass_spectrum",
]
