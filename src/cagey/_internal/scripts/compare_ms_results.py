import argparse
from collections.abc import Iterable
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
    old_results = _get_old_ms_results(args.csv_results)
    new_results = _get_new_ms_results(engine)
    summary = (
        old_results.join(
            new_results,
            on=[
                "experiment",
                "plate",
                "formulation_number",
                "di_count",
                "tri_count",
                "adduct",
                "charge",
            ],
            how="left",
        )
        .with_columns(
            spectrum_mz_diff=pl.col("spectrum_mz")
            .sub(pl.col("spectrum_mz_right"))
            .abs(),
            intensity_diff=pl.col("intensity")
            .sub(pl.col("intensity_right"))
            .abs(),
        )
        .filter(
            pl.col("spectrum_mz_diff")
            .is_null()
            .or_(pl.col("spectrum_mz_diff").gt(1e-8))
            .or_(pl.col("intensity_diff").is_null())
            .or_(pl.col("intensity_diff").gt(1e-8))
        )
    )
    print(
        summary.select(
            [
                "experiment",
                "plate",
                "formulation_number",
                "di_count",
                "tri_count",
                "adduct",
                "charge",
                "spectrum_mz",
                "intensity",
                "spectrum_mz_right",
                "intensity_right",
                "spectrum_mz_diff",
                "intensity_diff",
            ]
        ).collect()
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path, nargs="+")
    return parser.parse_args()


def _get_old_ms_results(paths: Iterable[Path]) -> pl.LazyFrame:
    return pl.concat(
        pl.scan_csv(path)
        .rename(
            {
                "Plate": "plate",
                "Intensity": "intensity",
                "Adduct": "adduct",
                "Charge": "charge",
                "Topology": "topology",
                "Position": "formulation_number",
                "M/Z Present?": "spectrum_mz",
            }
        )
        .filter(pl.col("Correct_Seperation?").eq(True))
        .filter(pl.col("adduct").is_not_null())
        .with_columns(
            experiment=pl.lit(path.stem),
            counts=pl.col("topology")
            .str.strip_chars("()")
            .str.split(", ")
            .list.eval(pl.element().cast(pl.Int64)),
        )
        .with_columns(
            tri_count=pl.col("counts").list.get(0),
            di_count=pl.col("counts").list.get(1),
        )
        for path in paths
    )


def _get_new_ms_results(engine: Engine) -> pl.LazyFrame:
    mass_spectra = (
        pl.read_database(
            "SELECT massspectrum.id, experiment, plate, formulation_number "
            "FROM massspectrum "
            "LEFT JOIN reaction "
            "ON massspectrum.reaction_id = reaction.id",
            engine.connect(),
        )
        .lazy()
        .rename({"id": "mass_spectrum_id"})
    )
    separation_peaks = pl.read_database(
        "SELECT * from separationmassspecpeak", engine.connect()
    ).lazy()
    return separation_peaks.join(
        mass_spectra, on="mass_spectrum_id", how="left"
    )


if __name__ == "__main__":
    main()
