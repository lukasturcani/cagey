import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from sqlalchemy.engine import Engine
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool


def main() -> None:
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(-1)
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    old = _get_old_nmr_results(map(OldData.from_path, args.csv_results))
    new = _get_new_nmr_results(engine)
    combined_summary = old.summary.join(
        new.summary,
        on=["experiment", "plate", "formulation_number"],
        how="left",
        suffix="_new",
    ).with_columns(
        match=(
            (pl.col("has_aldehyde") == pl.col("has_aldehyde_new"))
            & (pl.col("has_imine") == pl.col("has_imine_new"))
        ),
    )
    spectrum_results = combined_summary.group_by("match").agg(pl.count())
    print("imine / aldehyde found summary")
    print(spectrum_results.collect())
    print()

    aldehyde_peaks_not_found_in_new = (
        old.aldehyde_peaks.join_asof(
            new.aldehyde_peaks.rename({"ppm": "ppm_right"}),
            by=["experiment", "plate", "formulation_number"],
            left_on="ppm",
            right_on="ppm_right",
            strategy="nearest",
        )
        .with_columns(ppm_diff=(pl.col("ppm") - pl.col("ppm_right")).abs())
        .filter(pl.col("ppm_diff").is_null() | (pl.col("ppm_diff") > 1e-8))
    )
    print("aldehyde peaks not found in new")
    print(aldehyde_peaks_not_found_in_new.collect())
    print()

    imine_peaks_not_found_in_new = (
        old.aldehyde_peaks.join_asof(
            new.aldehyde_peaks.rename({"ppm": "ppm_right"}),
            by=["experiment", "plate", "formulation_number"],
            left_on="ppm",
            right_on="ppm_right",
            strategy="nearest",
        )
        .with_columns(ppm_diff=(pl.col("ppm") - pl.col("ppm_right")).abs())
        .filter(pl.col("ppm_diff").is_null() | (pl.col("ppm_diff") > 1e-8))
    )
    print("imine peaks not found in new")
    print(imine_peaks_not_found_in_new.collect())
    print()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path, nargs="+")
    return parser.parse_args()


@dataclass(frozen=True, slots=True)
class OldData:
    experiment: str
    path: Path

    @staticmethod
    def from_path(path: Path) -> "OldData":
        return OldData(path.stem, path)


@dataclass(frozen=True, slots=True)
class Results:
    summary: pl.LazyFrame
    aldehyde_peaks: pl.LazyFrame
    imine_peaks: pl.LazyFrame


def _get_old_nmr_results(paths: Iterable[OldData]) -> Results:
    results = pl.concat(
        pl.scan_csv(path.path)
        .rename(
            {
                "Plate": "plate",
                "Position": "formulation_number",
                "Aldehyde?": "has_aldehyde",
                "Imine?": "has_imine",
                "Aldehyde_Peaks": "aldehyde_peaks",
                "Imine_Peaks": "imine_peaks",
                "Aldehyde_Amplitudes": "aldehyde_amplitudes",
                "Imine_Amplitudes": "imine_amplitudes",
            }
        )
        .with_columns(experiment=pl.lit(path.experiment))
        for path in paths
    ).with_columns(
        pl.when(pl.col("experiment") == "AB-02-007")
        .then(pl.col("plate").map_dict({2: 4}, default=pl.first()))
        .otherwise(pl.col("plate"))
    )
    return Results(
        summary=results.select(
            [
                "experiment",
                "plate",
                "formulation_number",
                "has_aldehyde",
                "has_imine",
            ]
        ),
        aldehyde_peaks=_explode_peak_columns(
            results.select(
                [
                    "experiment",
                    "plate",
                    "formulation_number",
                    "aldehyde_peaks",
                    "aldehyde_amplitudes",
                ]
            ),
            "aldehyde_peaks",
            "aldehyde_amplitudes",
        ).rename(
            {"aldehyde_peaks": "ppm", "aldehyde_amplitudes": "amplitude"}
        ),
        imine_peaks=_explode_peak_columns(
            results.select(
                [
                    "experiment",
                    "plate",
                    "formulation_number",
                    "imine_peaks",
                    "imine_amplitudes",
                ]
            ),
            "imine_peaks",
            "imine_amplitudes",
        ).rename({"imine_peaks": "ppm", "imine_amplitudes": "amplitude"}),
    )


def _explode_peak_columns(
    df: pl.LazyFrame, ppm: str, amplitude: str
) -> pl.LazyFrame:
    return (
        df.with_columns(
            pl.col(ppm).str.strip_chars("[]"),
            pl.col(amplitude).str.strip_chars("[]"),
        )
        .filter(
            pl.col(ppm).is_not_null()
            & pl.col(amplitude).is_not_null()
            & (pl.col(ppm) != "")
            & (pl.col(amplitude) != "")
        )
        .with_columns(
            pl.col(ppm)
            .str.split(pl.lit(","))
            .list.eval(
                pl.element().str.strip_chars().cast(pl.Float64), parallel=True
            ),
            pl.col(amplitude)
            .str.split(pl.lit(","))
            .list.eval(
                pl.element().str.strip_chars().cast(pl.Float64), parallel=True
            ),
        )
        .explode([ppm, amplitude])
    )


def _get_new_nmr_results(engine: Engine) -> Results:
    aldehyde_peaks = pl.read_database(
        "SELECT nmr_spectrum_id, ppm, amplitude  FROM nmraldehydepeak",
        engine.connect(),
    ).lazy()
    has_aldehyde_peaks = aldehyde_peaks.unique("nmr_spectrum_id").with_columns(
        has_aldehyde=True
    )

    imine_peaks = pl.read_database(
        "SELECT nmr_spectrum_id, ppm, amplitude FROM nmriminepeak",
        engine.connect(),
    ).lazy()
    has_imine_peaks = imine_peaks.unique("nmr_spectrum_id").with_columns(
        has_imine=True
    )

    has_peaks = has_aldehyde_peaks.join(
        has_imine_peaks, on="nmr_spectrum_id", how="outer"
    ).fill_null(False)

    nmr_spectra = (
        pl.read_database(
            "SELECT nmrspectrum.id, experiment, plate, formulation_number "
            "FROM nmrspectrum "
            "LEFT JOIN reaction "
            "ON nmrspectrum.reaction_id = reaction.id",
            engine.connect(),
        )
        .lazy()
        .rename({"id": "nmr_spectrum_id"})
    )
    return Results(
        summary=nmr_spectra.join(has_peaks, on="nmr_spectrum_id", how="left"),
        aldehyde_peaks=aldehyde_peaks.join(
            nmr_spectra, on="nmr_spectrum_id", how="left"
        ),
        imine_peaks=imine_peaks.join(
            nmr_spectra, on="nmr_spectrum_id", how="left"
        ),
    )


if __name__ == "__main__":
    main()
