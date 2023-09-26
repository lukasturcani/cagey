import argparse
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path
from typing import Protocol

import numpy as np
import polars as pl
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

from cagey._internal.nmr import NmrSpectrum


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    old_results = pl.read_csv(args.csv_results)
    missing = 0
    not_missing = 0
    with Session(engine) as session:
        for row in old_results.rows(named=True):
            query = select(NmrSpectrum).where(
                NmrSpectrum.experiment == args.experiment,
                NmrSpectrum.machine_expriment == row["Title"],
                NmrSpectrum.plate == f'P{row["Plate"]}',
                NmrSpectrum.formulation_number == row["Position"],
            )
            nmr_spectrum = session.exec(query).one_or_none()
            if nmr_spectrum is None:
                missing += 1
                continue
            not_missing += 1
            csv_aldehyde_peaks = tuple(
                _get_peaks(
                    shifts=row["Aldehyde_Peaks"],
                    amplitudes=row["Aldehyde_Amplitudes"],
                )
            )
            aldhehyde_comparison = _compare_peaks(
                csv_aldehyde_peaks,
                tuple(map(Peak.from_, nmr_spectrum.aldehyde_peaks)),
            )
            assert len(aldhehyde_comparison.peaks_in_csv) == 0
            assert len(aldhehyde_comparison.peaks_in_database) == 0
            csv_imine_peaks = tuple(
                _get_peaks(
                    shifts=row["Imine_Peaks"],
                    amplitudes=row["Imine_Amplitudes"],
                )
            )
            imine_comparison = _compare_peaks(
                csv_imine_peaks,
                tuple(map(Peak.from_, nmr_spectrum.imine_peaks)),
            )
            assert len(imine_comparison.peaks_in_csv) == 0
            assert len(imine_comparison.peaks_in_database) == 0

    print(f"Missing: {missing}")
    print(f"Not missing: {not_missing}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment")
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


class PeakP(Protocol):
    @property
    def ppm(self) -> float:
        ...

    @property
    def amplitude(self) -> float:
        ...


@dataclass(frozen=True, slots=True)
class Peak:
    ppm: float
    amplitude: float

    @staticmethod
    def from_(peak: PeakP) -> "Peak":
        return Peak(peak.ppm, peak.amplitude)


@dataclass(frozen=True, slots=True)
class PeakMatch:
    csv_peak: PeakP
    database_peak: PeakP


@dataclass(frozen=True, slots=True)
class PeakComparison:
    peaks_in_both: list[PeakMatch]
    peaks_in_csv: list[PeakP]
    peaks_in_database: list[PeakP]


def _get_peaks(shifts: str | None, amplitudes: str | None) -> Iterator[Peak]:
    aldehyde_shifts = eval(shifts) if shifts is not None else []
    aldehyde_amplitudes = eval(amplitudes) if amplitudes is not None else []
    return map(Peak, aldehyde_shifts, aldehyde_amplitudes)


def _compare_peaks(
    csv_peaks: Sequence[PeakP],
    database_peaks: Sequence[PeakP],
) -> PeakComparison:
    peaks_in_both = []
    matched_database_peaks = set()
    matched_csv_peaks = set()
    for csv_peak in csv_peaks:
        for database_peak in database_peaks:
            if database_peak in matched_database_peaks:
                continue
            if np.isclose(csv_peak.ppm, database_peak.ppm):
                peaks_in_both.append(PeakMatch(csv_peak, database_peak))
                matched_database_peaks.add(database_peak)
                matched_csv_peaks.add(csv_peak)
                break
    peaks_in_csv = [
        peak for peak in csv_peaks if peak not in matched_csv_peaks
    ]
    peaks_in_database = [
        peak for peak in database_peaks if peak not in matched_database_peaks
    ]
    return PeakComparison(peaks_in_both, peaks_in_csv, peaks_in_database)


if __name__ == "__main__":
    main()
