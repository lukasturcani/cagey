import logging
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, replace
from operator import attrgetter
from pathlib import Path

import nmrglue
import numpy as np
from sqlmodel import Field, Relationship, Session, SQLModel

logger = logging.getLogger(__name__)


class NmrSpectrum(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    experiment: str
    plate: str
    machine_expriment: str
    formulation_number: int
    aldehyde_peaks: list["AldehydePeak"] = Relationship(
        back_populates="nmr_spectrum",
    )
    imine_peaks: list["IminePeak"] = Relationship(
        back_populates="nmr_spectrum"
    )


class AldehydePeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    nmr_spectrum: NmrSpectrum = Relationship(back_populates="aldehyde_peaks")
    ppm: float
    amplitude: float


class IminePeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nmr_spectrum_id: int = Field(foreign_key="nmrspectrum.id")
    nmr_spectrum: NmrSpectrum = Relationship(back_populates="imine_peaks")
    ppm: float
    amplitude: float


def add_data(nmr_path: Path, session: Session, commit: bool = True) -> None:
    for spectrum in nmr_path.glob("**/pdata/1/1r"):
        spectrum_dir = spectrum.parent
        try:
            title = spectrum_dir.joinpath("title").read_text()
            experiment, plate, formulation_number_ = title.split(",")
            formulation_number = int(formulation_number_)
        except ValueError:
            logger.error(
                "reading %s failed because of bad title %s",
                spectrum_dir,
                title,
            )
            continue

        nmr_spectrum = NmrSpectrum(
            title=title,
            experiment=experiment,
            plate=plate,
            machine_expriment=spectrum_dir.parent.parent.name,
            formulation_number=formulation_number,
        )

        try:
            # TODO: maybe - pick peaks twice so that 1e5 is used for aldehyde
            # and imine peaks.
            peaks = tuple(_pick_peaks(spectrum_dir))
        except ZeroDivisionError:
            logger.error(
                "reading %s failed with zero division error", spectrum_dir
            )
            continue

        reference_peak_ppm = 7.28
        possible_reference_peaks = filter(
            lambda peak: peak.has_ppm(reference_peak_ppm),
            peaks,
        )
        try:
            reference_peak = max(
                possible_reference_peaks,
                key=attrgetter("amplitude"),
            )
        except ValueError:
            logger.error(
                "%s has no reference peak at %s",
                spectrum_dir,
                reference_peak_ppm,
            )
            continue
        reference_shift = 7.26 - reference_peak.shift
        chloroform_peaks = [7.26, 7.52, 7.00]
        nmr_spectrum.aldehyde_peaks.extend(
            AldehydePeak(
                nmr_spectrum=nmr_spectrum,
                ppm=peak.shift,
                amplitude=peak.amplitude,
            )
            for peak in _get_aldehyde_peaks(
                peaks, reference_shift, chloroform_peaks
            )
        )
        nmr_spectrum.imine_peaks.extend(
            IminePeak(
                nmr_spectrum=nmr_spectrum,
                ppm=peak.shift,
                amplitude=peak.amplitude,
            )
            for peak in _get_imine_peaks(
                peaks, reference_shift, chloroform_peaks
            )
        )
        session.add(nmr_spectrum)
        if commit:
            session.commit()


@dataclass(frozen=True, slots=True)
class Peak:
    shift: float
    amplitude: float

    def in_range(self, min_ppm: float, max_ppm: float) -> bool:
        return min_ppm < self.shift < max_ppm

    def has_ppm(self, ppm: float, atol: float = 0.05) -> bool:
        return self.in_range(ppm - atol, ppm + atol)


def _pick_peaks(spectrum_dir: Path) -> Iterator[Peak]:
    metadata, data = nmrglue.bruker.read_pdata(str(spectrum_dir))
    udic = nmrglue.bruker.guess_udic(metadata, data)
    unit_conversion = nmrglue.fileio.fileiobase.uc_from_udic(udic)
    for peak in nmrglue.peakpick.pick(data, pthres=1e4, nthres=None):
        shift = unit_conversion.ppm(peak["X_AXIS"])
        amplitude = peak["VOL"]
        yield Peak(shift, amplitude)


def _shift_peaks(
    peaks: Iterable[Peak],
    shift: float,
) -> Iterator[Peak]:
    for peak in peaks:
        yield replace(peak, shift=peak.shift + shift)


def _remove_peaks(
    peaks: Iterable[Peak],
    to_remove: Sequence[float],
) -> Iterator[Peak]:
    for peak in peaks:
        if not np.any(np.isclose(peak.shift, to_remove, atol=0.02)):
            yield peak


def _get_aldehyde_peaks(
    peaks: Iterable[Peak],
    reference_shift: float,
    solvent_peaks: Sequence[float],
) -> Iterator[Peak]:
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
    peaks: Iterable[Peak],
    reference_shift: float,
    solvent_peaks: Sequence[float],
) -> Iterator[Peak]:
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
