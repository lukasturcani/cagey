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
    print(
        old_results.select(
            [
                "experiment",
                "plate",
                "formulation_number",
                "di_count",
                "tri_count",
                "adduct",
                "charge",
                "spectrum_mz",
            ]
        )
        .filter(
            (pl.col("plate") == pl.lit(1))
            & (pl.col("formulation_number") == pl.lit(9))
        )
        .collect()
    )
    print(
        new_results.select(
            [
                "experiment",
                "plate",
                "formulation_number",
                "di_count",
                "tri_count",
                "adduct",
                "charge",
                "spectrum_mz",
            ]
        )
        .filter(
            (pl.col("plate") == pl.lit(1))
            & (pl.col("formulation_number") == pl.lit(9))
        )
        .collect()
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
        .filter(pl.col("Correct_Seperation?"))
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
    mass_spectrums = (
        pl.read_database("SELECT * from massspectrum", engine.connect())
        .lazy()
        .rename({"id": "mass_spectrum_id"})
    )
    corrected_peaks = pl.read_database(
        "SELECT * from correctedmassspecpeak", engine.connect()
    ).lazy()
    return mass_spectrums.join(
        corrected_peaks, on="mass_spectrum_id", how="inner"
    )


if __name__ == "__main__":
    main()
