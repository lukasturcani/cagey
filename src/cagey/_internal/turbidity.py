import polars as pl

from cagey._internal.tables import TurbidState


def get_turbid_state(
    turbidities: dict[str, float], dissolved_reference: float
) -> TurbidState:
    turbidity = _turbidity_from_json(turbidities)
    turbidity = _average_turbidity(turbidity)
    turbidity = (
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
    )
    result = turbidity.collect()
    if result.is_empty():
        return TurbidState.NOT_DETERMINED
    if result.row(0, named=True)["mean_turbidity"] < dissolved_reference:
        return TurbidState.DISSOLVED
    return TurbidState.TURBID


def _turbidity_from_json(turbidity_json: dict[str, float]) -> pl.LazyFrame:
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


def _average_turbidity(turbidity: pl.LazyFrame) -> pl.LazyFrame:
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
