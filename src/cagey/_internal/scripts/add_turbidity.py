import argparse
import json
from enum import Enum, auto
from pathlib import Path
from typing import TypeAlias

import polars as pl

Json: TypeAlias = int | float | str | None | list["Json"] | dict[str, "Json"]


class TurbidState(Enum):
    DISSOLVED = auto()
    SATURATED = auto()
    STABLE = auto()
    UNSTABLE = auto()


class Category(Enum):
    DISSOLVED = auto()
    UNDISSOLVED = auto()
    NOT_DETERMINED = auto()


def main() -> None:
    pl.Config.set_tbl_rows(-1)
    pl.Config.set_tbl_cols(-1)
    args = _parse_args()
    for path in args.data:
        data = _read_json(path)
        dissolved_reference = data["turbidity_dissolved_reference"]
        turbidity = turbidity_from_json(data["turbidity_data"])
        turbidity = average_turbidity(turbidity)
        turbidity_result = (
            turbidity.with_columns(
                stable=pl.col("turbidity")
                .is_between(pl.col("lower_bound"), pl.col("upper_bound"))
                .or_(pl.col("turbidities").list.len() == 1),
            )
            .with_columns(
                group=(
                    (pl.col("stable") != pl.col("stable").shift(1))
                    .fill_null(value=True)
                    .cum_sum()
                ),
            )
            .group_by("group")
            .agg(
                time_delta=pl.max("time") - pl.min("time"),
                mean_turbidity=pl.mean("turbidity"),
            )
            .filter(
                pl.col("time_delta") >= pl.duration(minutes=1),
            )
        ).collect()
        if turbidity_result.is_empty():
            category = Category.NOT_DETERMINED
        elif (
            turbidity_result.row(0, named=True)["mean_turbidity"]
            < dissolved_reference
        ):
            category = Category.DISSOLVED
        else:
            category = Category.UNDISSOLVED

        print(category)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("data", type=Path, nargs="+")
    return parser.parse_args()


def _read_json(path: Path) -> Json:
    with path.open() as file:
        return json.load(file)


def turbidity_from_json(turbidity_json: dict[str, float]) -> pl.LazyFrame:
    return (
        pl.DataFrame(
            {
                "time": list(turbidity_json.keys()),
                "turbidity": list(turbidity_json.values()),
            }
        )
        .with_columns(
            pl.col("time").str.strptime(
                pl.Datetime, format="%Y_%m_%d_%H_%M_%S_%f"
            ),
        )
        .sort("time")
        .lazy()
    )


def average_turbidity(turbidity: pl.LazyFrame) -> pl.LazyFrame:
    return (
        turbidity.rolling("time", period="1m", offset="0", closed="both")
        .agg(
            turbidities=pl.col("turbidity"),
            mean=pl.mean("turbidity"),
            std=pl.std("turbidity"),
            lower_bound=pl.mean("turbidity") - 3 * pl.std("turbidity"),
            upper_bound=pl.mean("turbidity") + 3 * pl.std("turbidity"),
        )
        .join(turbidity, on="time")
    )
