import pkgutil
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from sqlite3 import Connection
from typing import Generic, TypeVar


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

T = TypeVar("T")


class Row(Generic[T]):
    id: int
    item: T


class CreateTablesError(Exception):
    pass


def create_tables(connection: Connection) -> None:
    script = pkgutil.get_data("cagey", "_internal/sql/create_tables.sql")
    if script is not None:
        connection.executescript(script.decode())
    else:
        msg = "failed to load create_tables.sql"
        raise CreateTablesError(msg)


def insert_mass_spectrum(
    connection: Connection,
    reaction_id: int,
    peaks: Iterable[MassSpectrumPeak],
    *,
    commit: bool = True,
) -> None:
    cursor = connection.execute(
        "INSERT INTO mass_spectra (reaction_id) VALUES (?)",
        (reaction_id,),
    )
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
            {cursor.lastrowid}
            :di_count,
            :tri_count,
            :adduct,
            :charge,
            :calculated_mz,
            :speectrum_mz,
            :separation_mz,
            :intensity
        )
        """,  # noqa: S608
        map(asdict, peaks),
    )
    if commit:
        connection.commit()
