import pkgutil
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict, astuple, dataclass
from enum import Enum
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

    @staticmethod
    def from_title_file(title_file: Path) -> "ReactionKey":
        title = title_file.read_text()
        experiment, plate, formulation_number = title.split("_")
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


@dataclass(frozen=True, slots=True)
class Row(Generic[T]):
    id: int
    item: T


class CreateTablesError(Exception):
    pass


class InsertMassSpectrumError(Exception):
    pass


class InsertNmrSpectrumError(Exception):
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
    reaction_key: ReactionKey,
    peaks: Iterable[MassSpectrumPeak],
    *,
    commit: bool = True,
) -> tuple[MassSpectrumId, MassSpectrumPeakId]:
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
    cursor.executemany(
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


@dataclass(frozen=True, slots=True)
class NmrPeak:
    ppm: float
    amplitude: float

    def in_range(self, min_ppm: float, max_ppm: float) -> bool:
        return min_ppm < self.ppm < max_ppm

    def has_ppm(self, ppm: float, atol: float = 0.05) -> bool:
        return self.in_range(ppm - atol, ppm + atol)


NmrSpectrumId = NewType("NmrSpectrumId", int)
NmrAldehydePeakId = NewType("NmrAldehydePeakId", int)
NmrIminePeakId = NewType("NmrIminePeakId", int)


@dataclass(frozen=True, slots=True)
class NmrSpectrum:
    aldehyde_peaks: Sequence[NmrPeak]
    imine_peaks: Sequence[NmrPeak]


def insert_nmr_spectrum(
    connection: Connection,
    reaction_key: ReactionKey,
    spectrum: NmrSpectrum,
    *,
    commit: bool = True,
) -> tuple[NmrSpectrumId, NmrAldehydePeakId, NmrIminePeakId]:
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

    cursor = connection.executemany(
        f"""
        INSERT INTO nmr_aldehyde_peaks (nmr_spectrum_id, ppm, amplitude)
        VALUES ({nmr_spectrum_id}, :ppm, :amplitude)
        """,  # noqa: S608
        map(asdict, spectrum.aldehyde_peaks),
    )
    _nmr_aldehyde_peak_id = cursor.lastrowid
    if isinstance(_nmr_aldehyde_peak_id, int):
        nmr_aldehyde_peak_id = NmrAldehydePeakId(_nmr_aldehyde_peak_id)
    else:
        msg = "failed to insert nmr aldehyde peaks"
        raise InsertNmrSpectrumError(msg)

    cursor = connection.executemany(
        f"""
        INSERT INTO nmr_imine_peaks (nmr_spectrum_id, ppm, amplitude)
        VALUES ({nmr_spectrum_id}, :ppm, :amplitude)
        """,  # noqa: S608
        map(asdict, spectrum.imine_peaks),
    )
    _nmr_imine_peak_id = cursor.lastrowid
    if isinstance(_nmr_imine_peak_id, int):
        nmr_imine_peak_id = NmrIminePeakId(_nmr_imine_peak_id)
    else:
        msg = "failed to insert nmr imine peaks"
        raise InsertNmrSpectrumError(msg)

    if commit:
        connection.commit()

    return (nmr_spectrum_id, nmr_aldehyde_peak_id, nmr_imine_peak_id)


class TurbidState(Enum):
    DISSOLVED = "dissolved"
    TURBID = "turbid"
    UNSTABLE = "unstable"


def insert_turbidity(  # noqa: PLR0913
    connection: Connection,
    reaction_key: ReactionKey,
    dissolved_reference: float,
    data: dict[str, float],
    turbidity_state: TurbidState,
    *,
    commit: bool = True,
) -> None:
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
            reaction | {"time": time, "turbidity": turbidity}
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
