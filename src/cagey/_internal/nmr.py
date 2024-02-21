from collections.abc import Iterable, Iterator, Sequence
from dataclasses import replace
from operator import attrgetter
from pathlib import Path

import nmrglue
import numpy as np

from cagey._internal.types import NmrPeak, NmrSpectrum


def get_spectrum(spectrum_dir: Path) -> NmrSpectrum:
    """Get NMR spectrum from the machine data directory.

    Parameters:
        spectrum_dir: Path to the directory containing the spectrum data.

    Returns:
        The NMR spectrum.
    """
    peaks = tuple(_pick_peaks(spectrum_dir))

    reference_peak_ppm = 7.28
    possible_reference_peaks = filter(
        lambda peak: peak.has_ppm(reference_peak_ppm),
        peaks,
    )
    reference_peak = max(
        possible_reference_peaks,
        key=attrgetter("amplitude"),
    )
    reference_shift = 7.26 - reference_peak.ppm
    chloroform_peaks = [7.26, 7.52, 7.00]
    return NmrSpectrum(
        aldehyde_peaks=tuple(
            _get_aldehyde_peaks(peaks, reference_shift, chloroform_peaks)
        ),
        imine_peaks=tuple(
            _get_imine_peaks(peaks, reference_shift, chloroform_peaks)
        ),
    )


def _pick_peaks(spectrum_dir: Path) -> Iterator[NmrPeak]:
    metadata, data = nmrglue.bruker.read_pdata(str(spectrum_dir))
    udic = nmrglue.bruker.guess_udic(metadata, data)
    unit_conversion = nmrglue.fileio.fileiobase.uc_from_udic(udic)
    for peak in nmrglue.peakpick.pick(data, pthres=1e4, nthres=None):
        shift = unit_conversion.ppm(peak["X_AXIS"])
        amplitude = peak["VOL"]
        yield NmrPeak(shift, amplitude)


def _shift_peaks(
    peaks: Iterable[NmrPeak],
    shift: float,
) -> Iterator[NmrPeak]:
    for peak in peaks:
        yield replace(peak, ppm=peak.ppm + shift)


def _remove_peaks(
    peaks: Iterable[NmrPeak],
    to_remove: Sequence[float],
) -> Iterator[NmrPeak]:
    for peak in peaks:
        if not np.any(np.isclose(peak.ppm, to_remove, atol=0.02)):
            yield peak


def _get_aldehyde_peaks(
    peaks: Iterable[NmrPeak],
    reference_shift: float,
    solvent_peaks: Sequence[float],
) -> Iterator[NmrPeak]:
    peaks = filter(
        lambda peak: peak.in_range(9.0, 11.0),
        peaks,
    )
    peaks = _shift_peaks(peaks, reference_shift)
    peaks = _remove_peaks(peaks, solvent_peaks)
    return filter(
        lambda peak: peak.amplitude > 0,
        peaks,
    )


def _get_imine_peaks(
    peaks: Iterable[NmrPeak],
    reference_shift: float,
    solvent_peaks: Sequence[float],
) -> Iterator[NmrPeak]:
    peaks = filter(
        lambda peak: peak.in_range(6.5, 9.0),
        peaks,
    )
    peaks = _shift_peaks(peaks, reference_shift)
    peaks = _remove_peaks(peaks, solvent_peaks)
    return filter(
        lambda peak: peak.amplitude > 0,
        peaks,
    )
