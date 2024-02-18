import pkgutil
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import Generic, NewType, TypeVar


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_ms_path(path: Path) -> "ReactionKey":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))


@dataclass(frozen=True, slots=True)
class MassSpectrumPeak:
    di_count: int
    tri_count: int
    adduct: str
    charge: int
    calculated_mz: float
    spectrum_mz: float
    separation_mz: float
    intensity: float


@dataclass(frozen=True, slots=True)
class MassSpectrumTopologyAssignment:
    mass_spectrum_peak_id: int
    topology: str


@dataclass(frozen=True, slots=True)
class Precursors:
    di_smiles: str
    tri_smiles: str


T = TypeVar("T")


class Row(Generic[T]):
    id: int
    item: T


class CreateTablesError(Exception):
    pass


class InsertMassSpectrumError(Exception):
    pass


def create_tables(connection: Connection) -> None:
    script = pkgutil.get_data("cagey", "_internal/sql/create_tables.sql")
    if script is not None:
        connection.executescript(script.decode())
    else:
        msg = "failed to load create_tables.sql"
        raise CreateTablesError(msg)


@dataclass(frozen=True, slots=True)
class Precursor:
    name: str
    smiles: str


def insert_precursors(
    connection: Connection,
    precursors: Iterable[Precursor],
    *,
    commit: bool = True,
) -> None:
    connection.executemany(
        "INSERT INTO precursors (name, smiles) VALUES (:name, :smiles)",
        map(asdict, precursors),
    )
    if commit:
        connection.commit()


@dataclass(frozen=True, slots=True)
class Reaction:
    experiment: str
    plate: int
    formulation_number: int
    di_name: str
    tri_name: str


def insert_reactions(
    connection: Connection,
    reactions: Iterable[Reaction],
    *,
    commit: bool = True,
) -> None:
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


MassSpectrumId = NewType("MassSpectrumId", int)
MassSpectrumPeakId = NewType("MassSpectrumPeakId", int)


def insert_mass_spectrum(
    connection: Connection,
    reaction_id: int,
    peaks: Iterable[MassSpectrumPeak],
    *,
    commit: bool = True,
) -> tuple[MassSpectrumId, MassSpectrumPeakId]:
    cursor = connection.execute(
        "INSERT INTO mass_spectra (reaction_id) VALUES (?)",
        (reaction_id,),
    )
    _mass_spectrum_id = cursor.lastrowid
    if isinstance(_mass_spectrum_id, int):
        mass_spectrum_id = MassSpectrumId(_mass_spectrum_id)
    else:
        msg = "failed to insert mass spectrum"
        raise InsertMassSpectrumError(msg)
    cursor.executemany(
        f"""
        INSERT INTO mass_spectrum_peaks (
            mass_spectrum_id,
            di_count,
            tri_count,
            adduct,
            charge,
            calculated_mz,
            speectrum_mz,
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
    _mass_spectrum_peak_id = cursor.lastrowid
    if isinstance(_mass_spectrum_peak_id, int):
        mass_spectrum_peak_id = MassSpectrumPeakId(_mass_spectrum_peak_id)
    else:
        msg = "failed to insert mass spectrum peaks"
        raise InsertMassSpectrumError(msg)

    if commit:
        connection.commit()

    return mass_spectrum_id, mass_spectrum_peak_id


def insert_mass_spectrum_topology_assignments(
    connection: Connection,
    assignments: Iterable[MassSpectrumTopologyAssignment],
    *,
    commit: bool = True,
) -> None:
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


def reaction_precursors(
    connection: Connection,
    reactions: Sequence[ReactionKey],
) -> Iterator[tuple[ReactionKey, Precursors]]:
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
            ON reactions.id = precursors.reaction_id
        LEFT JOIN
            precursors AS tri
            ON reactions.id = precursors.reaction_id
        WHERE
            (
                reactions.experiment,
                reactions.plate,
                reactions.formulation_number
            ) IN ({q})
        """,
        reactions,
    ):
        yield (
            ReactionKey(experiment, plate, formulation_number),
            Precursors(di_smiles, tri_smiles),
        )
