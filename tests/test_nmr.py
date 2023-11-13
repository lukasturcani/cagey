from operator import attrgetter
from pathlib import Path

import cagey
from cagey import Reaction


def test_nmr_extraction(datadir: Path) -> None:
    spectrum = cagey.nmr.get_spectrum(
        datadir / "NMR_data" / "AB-02-005" / "P1" / "170" / "pdata" / "1",
        Reaction(id=1, experiment="AB-02-005", plate=1, formulation_number=23),
    )
    aldehyde_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.aldehyde_peaks)
    )
    assert aldehyde_peaks == []
    imine_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.imine_peaks)
    )
    assert imine_peaks == []
