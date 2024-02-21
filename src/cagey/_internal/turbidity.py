import polars as pl

from cagey._internal.queries import TurbidState


def get_turbid_state(
    turbidities: dict[str, float], dissolved_reference: float
) -> TurbidState:
    """Get the turbidity state of an experiment.

    Parameters:
        turbidities:
            Maps a timestamp to a turbidity measurement.
        dissolved_reference:
            The turbidity at which the solution is considered dissolved.

    Returns:
        The turbidity state of the experiment.
    """
    turbidity = _turbidity_from_json(turbidities)
    turbidity = get_stability_windows(turbidity)
    turbidity = get_aggregated_stability_windows(turbidity)
    result = turbidity.collect()
    if result.is_empty():
        return TurbidState.UNSTABLE
    if result.row(0, named=True)["mean_turbidity"] < dissolved_reference + 1:
        return TurbidState.DISSOLVED
    return TurbidState.TURBID


def get_stability_windows(
    turbidity: pl.LazyFrame,
) -> pl.LazyFrame:
    """Get the stability windows for a turbidity measurement.

    Parameters:
        turbidity:
            A DataFrame with columns time and turbidity.

    Returns:
        A new DataFrame which groups the turbidity measurements into
        groups of 1 minute. Each group is then assigned a stability
        based on the mean turbidity and the standard deviation.
    """
    return (
        _average_turbidity(turbidity)
        .with_columns(
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
    )


def get_aggregated_stability_windows(
    turbidity: pl.LazyFrame,
) -> pl.LazyFrame:
    """Join adjacent windows with the same stability label.

    Parameters:
        turbidity:
            A DataFrame with rows representing 1 minute long windows
            each labeled according to stability.

    Returns:
        A new DataFrame which joins adjacent stability windows if
        they have the same stability.
    """
    return (
        turbidity.group_by("group")
        .agg(
            stable=pl.col("stable").first(),
            time_delta=pl.max("time") - pl.min("time"),
            mean_turbidity=pl.mean("turbidity"),
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
        )
        .join(turbidity, on="time")
    )
