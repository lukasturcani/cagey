import pkgutil
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, astuple
from datetime import datetime
from sqlite3 import Connection

import polars as pl

from cagey._internal.types import (
    MassSpectrumId,
    MassSpectrumPeak,
    MassSpectrumTopologyAssignment,
    NmrSpectrum,
    NmrSpectrumId,
    Precursor,
    Precursors,
    Reaction,
    ReactionKey,
    Row,
    TurbidState,
)


class CreateTablesError(Exception):
    """Raised when the tables cannot be created."""


class InsertMassSpectrumError(Exception):
    """Raised when a mass spectrum cannot be inserted."""


class InsertNmrSpectrumError(Exception):
    """Raised when an NMR spectrum cannot be inserted."""


def create_tables(connection: Connection) -> None:
    """Create the tables in the database.

    Parameters:
        connection: A SQLite connection.
    """
    script = pkgutil.get_data("cagey", "_internal/sql/create_tables.sql")
    if script is not None:
        connection.executescript(script.decode())
    else:
        msg = "failed to load create_tables.sql"
        raise CreateTablesError(msg)


def precursors_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of precursors.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of precursors.
    """
    return pl.read_database(
        """
      SELECT
          precursors.name,
          precursors.smiles
      FROM
          precursors
      ORDER BY
          precursors.name
      """,
        connection,
    )


def reactions_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of reactions.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of reactions.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name
      FROM
          reactions
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name,
          tri.name
      """,
        connection,
    )


def aldehyde_peaks_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of aldehyde peaks.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of aldehyde peaks.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          nmr_aldehyde_peaks.ppm,
          nmr_aldehyde_peaks.amplitude
      FROM
          nmr_aldehyde_peaks
      LEFT JOIN
          nmr_spectra
          ON nmr_aldehyde_peaks.nmr_spectrum_id = nmr_spectra.id
      LEFT JOIN
          reactions
          ON nmr_spectra.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          nmr_aldehyde_peaks.ppm
      """,
        connection,
    )


def imine_peaks_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of imine peaks.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of imine peaks.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          nmr_imine_peaks.ppm,
          nmr_imine_peaks.amplitude
      FROM
          nmr_imine_peaks
      LEFT JOIN
          nmr_spectra
          ON nmr_imine_peaks.nmr_spectrum_id = nmr_spectra.id
      LEFT JOIN
          reactions
          ON nmr_spectra.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          nmr_imine_peaks.ppm
      """,
        connection,
    )


def mass_spectrum_peaks_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of mass spectrum peaks.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of mass spectrum peaks.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          mass_spectrum_peaks.tri_count,
          mass_spectrum_peaks.di_count,
          mass_spectrum_peaks.adduct,
          mass_spectrum_peaks.charge,
          mass_spectrum_peaks.calculated_mz,
          mass_spectrum_peaks.spectrum_mz,
          mass_spectrum_peaks.separation_mz,
          mass_spectrum_peaks.intensity
      FROM
          mass_spectrum_peaks
      LEFT JOIN
          mass_spectra
          ON mass_spectrum_peaks.mass_spectrum_id = mass_spectra.id
      LEFT JOIN
          reactions
          ON mass_spectra.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          mass_spectrum_peaks.spectrum_mz
      """,
        connection,
    )


def mass_spectrum_topology_assignments_df(
    connection: Connection,
) -> pl.DataFrame:
    """Return a DataFrame of mass spectrum topology assignments.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of mass spectrum topology assignments.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          mass_spectrum_peaks.tri_count,
          mass_spectrum_peaks.di_count,
          mass_spectrum_peaks.adduct,
          mass_spectrum_peaks.charge,
          mass_spectrum_peaks.calculated_mz,
          mass_spectrum_peaks.spectrum_mz,
          mass_spectrum_peaks.separation_mz,
          mass_spectrum_peaks.intensity,
          mass_spectrum_topology_assignments.topology
      FROM
            mass_spectrum_topology_assignments
      LEFT JOIN
          mass_spectrum_peaks
          ON mass_spectrum_peaks.id =
            mass_spectrum_topology_assignments.mass_spectrum_peak_id
      LEFT JOIN
          mass_spectra
          ON mass_spectrum_peaks.mass_spectrum_id = mass_spectra.id
      LEFT JOIN
          reactions
          ON mass_spectra.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          mass_spectrum_peaks.spectrum_mz
        """,
        connection,
    )


def turbidity_dissolved_references_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of turbidity dissolved references.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of turbidity dissolved references.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          turbidity_dissolved_references.dissolved_reference
      FROM
          turbidity_dissolved_references
      LEFT JOIN
          reactions
          ON turbidity_dissolved_references.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number
      """,
        connection,
    )


def turbidity_measurements_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of turbidity measurements.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of turbidity measurements.
    """
    return (
        pl.read_database(
            """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          turbidity_measurements.time,
          turbidity_measurements.turbidity
      FROM
          turbidity_measurements
      LEFT JOIN
          reactions
          ON turbidity_measurements.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          turbidity_measurements.time
      """,
            connection,
        )
        .with_columns(
            pl.col("time").str.to_datetime(),
        )
        .sort(["experiment", "plate", "formulation_number", "time"])
    )


def turbidity_states_df(connection: Connection) -> pl.DataFrame:
    """Return a DataFrame of turbidity states.

    Parameters:
        connection: A SQLite connection.

    Returns:
        A DataFrame of turbidity states.
    """
    return pl.read_database(
        """
      SELECT
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number,
          di.name AS di_name,
          tri.name AS tri_name,
          turbidities.state
      FROM
          turbidities
      LEFT JOIN
          reactions
          ON turbidities.reaction_id = reactions.id
      LEFT JOIN
          precursors AS di
          ON reactions.di_name = di.name
      LEFT JOIN
          precursors AS tri
          ON reactions.tri_name = tri.name
      ORDER BY
          reactions.experiment,
          reactions.plate,
          reactions.formulation_number
      """,
        connection,
    )


def insert_precursors(
    connection: Connection,
    precursors: Iterable[Precursor],
    *,
    commit: bool = True,
) -> None:
    """Insert precursors into the database.

    Parameters:
        connection: A SQLite connection.
        precursors: The precursors to insert.
        commit: Whether to commit the transaction.
    """
    connection.executemany(
        "INSERT INTO precursors (name, smiles) VALUES (:name, :smiles)",
        map(asdict, precursors),
    )
    if commit:
        connection.commit()


def insert_reactions(
    connection: Connection,
    reactions: Iterable[Reaction],
    *,
    commit: bool = True,
) -> None:
    """Insert reactions into the database.

    Parameters:
        connection: A SQLite connection.
        reactions: The reactions to insert.
        commit: Whether to commit the transaction.
    """
    connection.executemany(
        """
        INSERT INTO reactions (
            experiment,
            plate,
            formulation_number,
            di_name,
            tri_name
        ) VALUES (
            :experiment,
            :plate,
            :formulation_number,
            :di_name,
            :tri_name
        )
        """,
        map(asdict, reactions),
    )
    if commit:
        connection.commit()


def insert_mass_spectrum(
    connection: Connection,
    reaction_key: ReactionKey,
    peaks: Sequence[MassSpectrumPeak],
    *,
    commit: bool = True,
) -> None:
    """Insert a mass spectrum into the database.

    Parameters:
        connection: A SQLite connection.
        reaction_key: The reaction key.
        peaks: The mass spectrum peaks.
        commit: Whether to commit the transaction.
    """
    cursor = connection.execute(
        """
        INSERT INTO
            mass_spectra (reaction_id)
        SELECT
            id
        FROM
            reactions
        WHERE
            experiment = :experiment
            AND plate = :plate
            AND formulation_number = :formulation_number
        """,
        asdict(reaction_key),
    )
    _mass_spectrum_id = cursor.lastrowid
    if isinstance(_mass_spectrum_id, int):
        mass_spectrum_id = MassSpectrumId(_mass_spectrum_id)
    else:
        msg = "failed to insert mass spectrum"
        raise InsertMassSpectrumError(msg)
    connection.executemany(
        f"""
        INSERT INTO mass_spectrum_peaks (
            mass_spectrum_id,
            di_count,
            tri_count,
            adduct,
            charge,
            calculated_mz,
            spectrum_mz,
            separation_mz,
            intensity
        ) VALUES (
            {mass_spectrum_id},
            :di_count,
            :tri_count,
            :adduct,
            :charge,
            :calculated_mz,
            :spectrum_mz,
            :separation_mz,
            :intensity
        )
        """,  # noqa: S608
        map(asdict, peaks),
    )

    if commit:
        connection.commit()


def insert_mass_spectrum_topology_assignments(
    connection: Connection,
    assignments: Iterable[MassSpectrumTopologyAssignment],
    *,
    commit: bool = True,
) -> None:
    """Insert mass spectrum topology assignments into the database.

    Parameters:
        connection: A SQLite connection.
        assignments: The mass spectrum topology assignments.
        commit: Whether to commit the transaction.
    """
    connection.executemany(
        """
        INSERT INTO mass_spectrum_topology_assignments (
            mass_spectrum_peak_id,
            topology
        ) VALUES (
            :mass_spectrum_peak_id,
            :topology
        )
        """,
        map(asdict, assignments),
    )
    if commit:
        connection.commit()


def mass_spectrum_peaks(
    connection: Connection,
    reaction_key: ReactionKey,
) -> Iterator[Row[MassSpectrumPeak]]:
    """Get the mass spectrum peaks for a reaction.

    Parameters:
        connection: A SQLite connection.
        reaction_key: The reaction key.
    """
    for (
        id_,
        di_count,
        tri_count,
        adduct,
        charge,
        calculated_mz,
        spectrum_mz,
        separation_mz,
        intensity,
    ) in connection.execute(
        """
        SELECT
            mass_spectrum_peaks.id,
            mass_spectrum_peaks.di_count,
            mass_spectrum_peaks.tri_count,
            mass_spectrum_peaks.adduct,
            mass_spectrum_peaks.charge,
            mass_spectrum_peaks.calculated_mz,
            mass_spectrum_peaks.spectrum_mz,
            mass_spectrum_peaks.separation_mz,
            mass_spectrum_peaks.intensity
        FROM
            mass_spectrum_peaks
        JOIN
            mass_spectra
            ON mass_spectra.id = mass_spectrum_peaks.mass_spectrum_id
        JOIN
            reactions
            ON mass_spectra.reaction_id = reactions.id
        WHERE
            reactions.experiment = :experiment
            AND reactions.plate = :plate
            AND reactions.formulation_number = :formulation_number
        """,
        asdict(reaction_key),
    ):
        yield Row(
            id_,
            MassSpectrumPeak(
                di_count=di_count,
                tri_count=tri_count,
                adduct=adduct,
                charge=charge,
                calculated_mz=calculated_mz,
                spectrum_mz=spectrum_mz,
                separation_mz=separation_mz,
                intensity=intensity,
            ),
        )


def reaction_precursors(
    connection: Connection,
    reactions: Sequence[ReactionKey],
) -> Iterator[tuple[ReactionKey, Precursors]]:
    """Get the precursors for a set of reactions.

    Parameters:
        connection: A SQLite connection.
        reactions: The reactions.
    """
    q = ",".join("(?,?,?)" for _ in range(len(reactions)))
    for (
        experiment,
        plate,
        formulation_number,
        di_smiles,
        tri_smiles,
    ) in connection.execute(
        f"""
        SELECT
            reactions.experiment,
            reactions.plate,
            reactions.formulation_number,
            di.smiles AS di_smiles,
            tri.smiles AS tri_smiles
        FROM
            reactions
        LEFT JOIN
            precursors AS di
            ON reactions.di_name = di.name
        LEFT JOIN
            precursors AS tri
            ON reactions.tri_name = tri.name
        WHERE
            (
                reactions.experiment,
                reactions.plate,
                reactions.formulation_number
            ) IN ({q})
        """,
        tuple(value for reaction in reactions for value in astuple(reaction)),
    ):
        yield (
            ReactionKey(experiment, plate, formulation_number),
            Precursors(di_smiles, tri_smiles),
        )


def insert_nmr_spectrum(
    connection: Connection,
    reaction_key: ReactionKey,
    spectrum: NmrSpectrum,
    *,
    commit: bool = True,
) -> None:
    """Insert an NMR spectrum into the database.

    Parameters:
        connection: A SQLite connection.
        reaction_key: The reaction key.
        spectrum: The NMR spectrum.
        commit: Whether to commit the transaction.
    """
    cursor = connection.execute(
        """
        INSERT INTO
            nmr_spectra (reaction_id)
        SELECT
            id
        FROM
            reactions
        WHERE
            experiment = :experiment
            AND plate = :plate
            AND formulation_number = :formulation_number
        """,
        asdict(reaction_key),
    )
    _nmr_spectrum_id = cursor.lastrowid
    if isinstance(_nmr_spectrum_id, int):
        nmr_spectrum_id = NmrSpectrumId(_nmr_spectrum_id)
    else:
        msg = "failed to insert nmr spectrum"
        raise InsertNmrSpectrumError(msg)

    connection.executemany(
        f"""
        INSERT INTO nmr_aldehyde_peaks (nmr_spectrum_id, ppm, amplitude)
        VALUES ({nmr_spectrum_id}, :ppm, :amplitude)
        """,  # noqa: S608
        map(asdict, spectrum.aldehyde_peaks),
    )
    connection.executemany(
        f"""
        INSERT INTO nmr_imine_peaks (nmr_spectrum_id, ppm, amplitude)
        VALUES ({nmr_spectrum_id}, :ppm, :amplitude)
        """,  # noqa: S608
        map(asdict, spectrum.imine_peaks),
    )

    if commit:
        connection.commit()


def insert_turbidity(  # noqa: PLR0913
    connection: Connection,
    reaction_key: ReactionKey,
    dissolved_reference: float,
    data: dict[str, float],
    turbidity_state: TurbidState,
    *,
    commit: bool = True,
) -> None:
    """Insert turbidity data into the database.

    Parameters:
        connection: A SQLite connection.
        reaction_key: The reaction key.
        dissolved_reference: The dissolved reference.
        data: A map of times to turbidity values.
        turbidity_state: The turbidity state.
        commit: Whether to commit the transaction.
    """
    reaction = asdict(reaction_key)
    connection.execute(
        """
        INSERT INTO
            turbidity_dissolved_references (reaction_id, dissolved_reference)
        SELECT
            id, :dissolved_reference
        FROM
            reactions
        WHERE
            experiment = :experiment
            AND plate = :plate
            AND formulation_number = :formulation_number
        """,
        reaction | {"dissolved_reference": dissolved_reference},
    )
    connection.executemany(
        """
        INSERT INTO
            turbidity_measurements (reaction_id, time, turbidity)
        SELECT
            id, :time, :turbidity
        FROM
            reactions
        WHERE
            experiment = :experiment
            AND plate = :plate
            AND formulation_number = :formulation_number
        """,
        (
            reaction
            | {
                "time": datetime.strptime(
                    time, "%Y_%m_%d_%H_%M_%S_%f"
                ).astimezone(),
                "turbidity": turbidity,
            }
            for time, turbidity in data.items()
        ),
    )
    connection.execute(
        """
            INSERT INTO
                turbidities (reaction_id, state)
            SELECT
                id, :state
            FROM
                reactions
            WHERE
                experiment = :experiment
                AND plate = :plate
                AND formulation_number = :formulation_number
            """,
        reaction | {"state": turbidity_state.value},
    )

    if commit:
        connection.commit()
