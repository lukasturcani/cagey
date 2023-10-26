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
    summary = old_results.join(
        new_results,
        on=["experiment", "plate", "formulation_number"],
        how="left",
    ).with_columns(
        match=(
            pl.col("topology").list.sort()
            == pl.col("topology_right").list.sort()
        )
        | (pl.col("topology").is_null() == pl.col("topology_right").is_null()),
    )
    print(
        summary.collect().filter(
            pl.col("match").eq(False) | pl.col("match").is_null()
        )
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


def _get_old_ms_results(path: Path) -> pl.LazyFrame:
    return (
        pl.scan_csv(path)
        .rename(
            {
                "Experiment_Name": "experiment",
                "Formulation_Number": "formulation_number",
                "Plate_Name": "plate",
                "Topology": "topology",
            }
        )
        .with_columns(
            pl.col("plate")
            .str.strip_prefix("PLATE")
            .str.replace("2B", "4")
            .cast(pl.Int64),
            pl.col("topology").str.strip_chars("[]").str.split(", "),
        )
    )


def _get_new_ms_results(engine: Engine) -> pl.LazyFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, topology "
            "FROM massspectopologyassignment "
            "LEFT JOIN massspecpeak "
            "ON mass_spec_peak_id = massspecpeak.id "
            "LEFT JOIN massspectrum "
            "ON mass_spectrum_id = massspectrum.id "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id",
            engine.connect(),
        )
        .group_by(["experiment", "plate", "formulation_number"])
        .agg(pl.col("topology").unique())
    ).lazy()


if __name__ == "__main__":
    main()
