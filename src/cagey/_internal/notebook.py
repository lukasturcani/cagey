import polars as pl

from cagey._internal.turbidity import (
    get_aggregated_stability_windows,
    get_stability_windows,
)


def get_ms_topology_assignments_from_database() -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, di_name, "
            "       tri_name, adduct, charge, calculated_mz, spectrum_mz, "
            "       separation_mz, intensity, topology "
            "FROM massspectopologyassignment "
            "LEFT JOIN massspecpeak "
            "ON mass_spec_peak_id = massspecpeak.id "
            "LEFT JOIN massspectrum "
            "ON mass_spectrum_id = massspectrum.id "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id",
            engine.connect(),
        )
        .sort(["experiment", "plate", "formulation_number"])
        .with_columns(
            ppm_error=get_ppm_error(),
            separation=get_separation(),
        )
    )


def get_nmr_aldehyde_peaks_from_database() -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, di_name, tri_name, "
        "       ppm, amplitude "
        "FROM nmraldehydepeak "
        "LEFT JOIN nmrspectrum "
        "ON nmr_spectrum_id = nmrspectrum.id "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_nmr_imine_peaks_from_database() -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, di_name, tri_name, "
        "       ppm, amplitude "
        "FROM nmriminepeak "
        "LEFT JOIN nmrspectrum "
        "ON nmr_spectrum_id = nmrspectrum.id "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_reactions_from_database() -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, "
        "       di_name, di.smiles AS di_smiles, "
        "tri_name, tri.smiles AS tri_smiles "
        "FROM reaction "
        "LEFT JOIN precursor di "
        "ON di.name = reaction.di_name "
        "LEFT JOIN precursor tri "
        "ON tri.name = reaction.tri_name",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_ms_peaks_from_database() -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, di_name, "
            "       tri_name, adduct, charge, calculated_mz, spectrum_mz, "
            "       separation_mz, intensity "
            "FROM massspecpeak "
            "LEFT JOIN massspectrum "
            "ON mass_spectrum_id = massspectrum.id "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id",
            engine.connect(),
        )
        .sort(["experiment", "plate", "formulation_number"])
        .with_columns(
            ppm_error=get_ppm_error(),
            separation=get_separation(),
        )
    )


def get_ppm_error() -> pl.Expr:
    return (
        (pl.col("calculated_mz") - pl.col("spectrum_mz"))
        / pl.col("calculated_mz")
        * pl.lit(1e6)
    ).abs()


def get_separation() -> pl.Expr:
    return (pl.col("separation_mz") - pl.col("spectrum_mz")) - (
        1 / pl.col("charge")
    )


def get_turbidity_from_database() -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, state "
        "FROM turbidity "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_turbidity_dissolved_reference_from_database() -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, dissolved_reference "
        "FROM turbiditydissolvedreference "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_turbidity_measurements_from_database() -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, time, turbidity "
            "FROM turbiditymeasurement "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id ",
            engine.connect(),
        )
        .with_columns(
            pl.col("time").str.strptime(
                pl.Datetime, format="%Y_%m_%d_%H_%M_%S_%f"
            ),
        )
        .sort("time")
    )


def get_turbidity_stability_windows_from_database() -> pl.DataFrame:
    turbidities = (
        pl.read_database(
            "SELECT time, turbidity "
            "FROM turbiditymeasurement "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id "
            "WHERE experiment = :experiment "
            "AND plate = :plate "
            "AND formulation_number = :formulation_number",
            engine.connect(),
            execute_options={
                "parameters": {
                    "experiment": experiment,
                    "plate": plate,
                    "formulation_number": formulation_number,
                }
            },
        )
        .lazy()
        .with_columns(
            pl.col("time").str.strptime(
                pl.Datetime, format="%Y_%m_%d_%H_%M_%S_%f"
            ),
        )
        .sort("time")
    )
    return get_stability_windows(turbidities).collect()


def get_turbidity_aggregated_stability_windows_from_database() -> pl.DataFrame:
    turbidities = (
        pl.read_database(
            "SELECT time, turbidity "
            "FROM turbiditymeasurement "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id "
            "WHERE experiment = :experiment "
            "AND plate = :plate "
            "AND formulation_number = :formulation_number",
            engine.connect(),
            execute_options={
                "parameters": {
                    "experiment": experiment,
                    "plate": plate,
                    "formulation_number": formulation_number,
                }
            },
        )
        .lazy()
        .with_columns(
            pl.col("time").str.strptime(
                pl.Datetime, format="%Y_%m_%d_%H_%M_%S_%f"
            ),
        )
        .sort("time")
    )
    turbidities = get_stability_windows(turbidities)
    return get_aggregated_stability_windows(turbidities).collect()
