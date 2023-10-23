from operator import attrgetter
from pathlib import Path

import cagey
from cagey import Reaction


def test_nmr_extraction(datadir: Path) -> None:
    spectrum = cagey.nmr.get_spectrum(
        datadir / "AB-02-005" / "P1" / "230" / "pdata" / "1",
        Reaction(id=1, experiment="AB-02-005", plate=1, formulation_number=23),
    )
    aldehyde_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.aldehyde_peaks)
    )
    assert aldehyde_peaks == [
        (
            9.085202304063953,
            31739.5703125,
        ),
        (
            9.087647317197327,
            71858.1640625,
        ),
        (
            9.091926090180733,
            10483.015625,
        ),
    ]
    imine_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.aldehyde_peaks)
    )
    assert imine_peaks == []
