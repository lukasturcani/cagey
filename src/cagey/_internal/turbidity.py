import polars as pl

from cagey._internal.tables import TurbidState


def get_turbid_state(
    turbidities: dict[str, float], dissolved_reference: float
) -> TurbidState:
    turbidity = _turbidity_from_json(turbidities)
    stable = (
        turbidity.select(
            pl.col("turbidity").max() - pl.col("turbidity").min() < pl.lit(3.0)
        )
        .collect()
        .item()
    )
    if stable:
        all_below_reference = (
            turbidity.filter(pl.col("turbidity") > dissolved_reference - 1.0)
            .collect()
            .is_empty()
        )
        if all_below_reference:
            return TurbidState.DISSOLVED
        all_above_reference = (
            turbidity.filter(pl.col("turbidity") < dissolved_reference + 3.0)
            .collect()
            .is_empty()
        )
        if all_above_reference:
            return TurbidState.TURBID

    turbidity = get_stability_windows(turbidity)
    turbidity = get_aggregated_stability_windows(turbidity)
    result = turbidity.collect()
    if result.is_empty():
        return TurbidState.UNSTABLE
    row = result.row(0, named=True)
    if row["mean_turbidity"] < dissolved_reference + 1.0:
        return TurbidState.DISSOLVED
    return TurbidState.TURBID


def get_stability_windows(
    turbidity: pl.LazyFrame,
) -> pl.LazyFrame:
    return (
        _average_turbidity(turbidity)
        .with_columns(
            # stable=pl.col("turbidity")
            # .is_between(pl.col("lower_bound"), pl.col("upper_bound"))
            # .or_(pl.col("turbidities").list.len() == 1),
            stable=pl.col("max") - pl.col("min") < pl.lit(3),
        )
        .with_columns(
            group=(
                (pl.col("stable") != pl.col("stable").shift(1))
                .fill_null(value=True)
                .cum_sum()
            ),
        )
    )


def get_aggregated_stability_windows(
    turbidity: pl.LazyFrame,
) -> pl.LazyFrame:
    return (
        turbidity.group_by("group")
        .agg(
            stable=pl.col("stable").first(),
            time_delta=pl.max("time") - pl.min("time"),
            mean_turbidity=pl.mean("turbidity"),
            std=pl.std("turbidity"),
        )
        .filter(
            pl.col("stable").eq(other=True),
            pl.col("time_delta") >= pl.duration(minutes=1),
        )
    )


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
            min=pl.min("turbidity"),
            max=pl.max("turbidity"),
        )
        .join(turbidity, on="time")
    )
