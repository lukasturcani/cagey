# ruff: noqa: T201

import argparse
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
    old_results = _get_old_results(args.csv_results)
    new_results = _get_new_results(engine)
    results = (
        old_results.join(
            new_results,
            on=["experiment", "plate", "formulation_number"],
            how="left",
        )
        .with_columns(
            match=(pl.col("state") == pl.col("state_right")).fill_null(
                value=False
            ),
            human_match=(
                pl.col("human_state") == pl.col("state_right")
            ).fill_null(value=False),
        )
        .filter(
            pl.col("match").eq(other=False)
            | pl.col("human_match").eq(other=False)
        )
        .sort(["experiment", "plate", "formulation_number"])
        .select(
            [
                "experiment",
                "plate",
                "formulation_number",
                "state",
                "state_right",
                "match",
            ]
        )
    )
    print(results.collect())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


def _get_old_results(path: Path) -> pl.LazyFrame:
    return (
        pl.scan_csv(path)
        .rename(
            {
                "Experiment_Name": "experiment",
                "Plate_Name": "plate",
                "Formulation_Number": "formulation_number",
                "Turbid_State": "state",
                "Turbid": "human_state",
            }
        )
        .with_columns(
            pl.col("plate").str.strip_prefix("PLATE").cast(pl.Int64),
            pl.col("state").map_dict(
                {
                    "dissolved": "DISSOLVED",
                    "undissolved": "TURBID",
                },
            ),
            pl.col("human_state").map_dict(
                {
                    True: "TURBID",
                    False: "DISSOLVED",
                }
            ),
        )
    )


def _get_new_results(engine: Engine) -> pl.LazyFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, state "
        "FROM turbidity "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).lazy()
