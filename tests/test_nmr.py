from operator import attrgetter
from pathlib import Path

import cagey


def test_nmr_extraction(datadir: Path) -> None:
    spectrum = cagey.nmr.get_spectrum(
        datadir / "NMR_data" / "AB-02-005" / "P1" / "170" / "pdata" / "1",
    )
    aldehyde_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.aldehyde_peaks)
    )
    assert aldehyde_peaks == []
    imine_peaks = sorted(
        map(attrgetter("ppm", "amplitude"), spectrum.imine_peaks)
    )
    assert imine_peaks == sorted(
        [
            (8.24472903946652, 21402.3671875),
            (8.184214964415505, 12020027.3828125),
            (8.157931073231731, 10329.4296875),
            (7.65181335462324, 10373.234375),
            (7.6499795947732085, 10029.46875),
            (7.589465519722193, 19573283.65625),
            (7.384695669802092, 384487.59375),
        ]
    )
