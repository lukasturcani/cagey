from pathlib import Path

import cagey
from cagey import Reaction


def test_nmr_extraction(datadir: Path) -> None:
    spectrum = cagey.nmr.get_spectrum(
        datadir / "NMR_data" / "AB-02-005" / "P1" / "230" / "pdata" / "1",
        Reaction(id=1, experiment="AB-02-005", plate=1, formulation_number=23),
    )
    assert len(spectrum.aldehyde_peaks) == 3
    assert len(spectrum.imine_peaks) == 35
