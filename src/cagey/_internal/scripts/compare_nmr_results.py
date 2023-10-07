import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from sqlalchemy.engine import Engine
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    old = _get_old_nmr_results(map(OldData.from_path, args.csv_results))
    new = _get_new_nmr_results(engine)
    combined = old.join(
        new,
        on=["experiment", "plate", "formulation_number"],
        how="outer",
        suffix="_new",
    ).with_columns(
        match=(
            (pl.col("has_aldehyde") == pl.col("has_aldehyde_new"))
            & (pl.col("has_imine") == pl.col("has_imine_new"))
        ),
    )
    summary = combined.group_by("match").agg(pl.count()).collect()
    print(summary)


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


def _get_old_nmr_results(paths: Iterable[OldData]) -> pl.LazyFrame:
    return pl.concat(
        pl.scan_csv(path.path)
        .rename(
            {
                "Plate": "plate",
                "Position": "formulation_number",
                "Aldehyde?": "has_aldehyde",
                "Imine?": "has_imine",
            }
        )
        .with_columns(experiment=pl.lit(path.experiment))
        for path in paths
    )


def _get_new_nmr_results(engine: Engine) -> pl.LazyFrame:
    has_aldehyde_peaks = (
        pl.read_database(
            "SELECT nmr_spectrum_id FROM nmraldehydepeak", engine.connect()
        )
        .lazy()
        .unique("nmr_spectrum_id")
        .with_columns(has_aldehyde=True)
    )
    has_imine_peaks = (
        pl.read_database(
            "SELECT nmr_spectrum_id FROM nmriminepeak", engine.connect()
        )
        .lazy()
        .unique("nmr_spectrum_id")
        .with_columns(has_imine=True)
    )
    has_peaks = has_aldehyde_peaks.join(
        has_imine_peaks, on="nmr_spectrum_id", how="outer"
    ).fill_null(False)
    return (
        pl.read_database(
            "SELECT id, experiment, plate, formulation_number "
            "FROM nmrspectrum ",
            engine.connect(),
        )
        .lazy()
        .rename({"id": "nmr_spectrum_id"})
        .join(has_peaks, on="nmr_spectrum_id", how="left")
        .drop("nmr_spectrum_id")
    )


if __name__ == "__main__":
    main()
