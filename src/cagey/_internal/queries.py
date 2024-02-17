import pkgutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path
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

T = TypeVar("T")

class Row(Generic[T]):
    id: int
    item: T


class CreateTablesError(Exception):
    pass


def create_tables(database: Path) -> None:
    connection = sqlite3.connect(database)
    script = pkgutil.get_data("cagey", "_internal/sql/create_tables.sql")
    if script is not None:
        connection.executescript(script.decode())
    else:
        msg = "failed to load create_tables.sql"
        raise CreateTablesError(msg)
