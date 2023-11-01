import argparse
import pkgutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any

from parallelbar import progress_imapu
from sqlalchemy.orm import aliased
from sqlmodel import Session, SQLModel, and_, create_engine, or_, select
from sqlmodel.pool import StaticPool

import cagey
from cagey import Precursor, Reaction

Di = aliased(Precursor)
Tri = aliased(Precursor)


def main() -> None:
    if __name__ == "__main__":
        args = _parse_args()
        to_csv = partial(_to_csv, args.mzmine)
        progress_imapu(to_csv, args.machine_data)


def old_main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    reaction_keys = tuple(map(ReactionKey.from_path, args.csv))
    reaction_query = select(Reaction, Di, Tri).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )

    spectrums = []
    with Session(engine) as session:
        reactions = {
            ReactionKey.from_reaction(result[0]): result
            for result in session.exec(reaction_query).all()
        }
        for path, reaction_key in zip(args.csv, reaction_keys, strict=True):
            reaction, di, tri = reactions[reaction_key]
            spectrum = cagey.ms.get_spectrum(path, reaction, di, tri)
            spectrums.append(spectrum)
            session.add(spectrum)
        session.commit()

        for spectrum in spectrums:
            session.add_all(cagey.ms.get_topologies(spectrum))
        session.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("machine_data", type=Path, nargs="+")
    parser.add_argument(
        "--mzmine",
        type=Path,
        default=Path("MZmine"),
        help="path to MZmine version 3.4",
    )
    return parser.parse_args()


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionKey":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_reaction(reaction: Reaction) -> "ReactionKey":
        return ReactionKey(
            reaction.experiment, reaction.plate, reaction.formulation_number
        )


def _get_reaction_query(reaction_key: ReactionKey) -> Any:
    return and_(
        Reaction.experiment == reaction_key.experiment,
        Reaction.plate == reaction_key.plate,
        Reaction.formulation_number == reaction_key.formulation_number,
        Di.name == Reaction.di_name,
        Tri.name == Reaction.tri_name,
    )


def _to_mzml(
    machine_data: Path,
) -> Path:
    subprocess.run(
        [
            "docker",
            "run",
            "-it",
            "--rm",
            "--env",
            "WINEDEBUG=-all",
            "--volume",
            f"{machine_data.resolve().parent}:/data",
            "chambm/pwiz-skyline-i-agree-to-the-vendor-licenses",
            "wine",
            "msconvert",
            str(machine_data.name),
            "-o",
            ".",
        ],
        check=True,
        capture_output=True,
    )
    return machine_data.parent / f"{machine_data.stem}.mzML"


def _mzml_to_csv(mzml: Path, mzmine: Path) -> None:
    template = pkgutil.get_data(
        "cagey", "_internal/scripts/mzmine_input_template.xml"
    )
    assert template is not None
    input_file_content = (
        template.decode()
        .replace("$INFILE$", str(mzml))
        .replace("$OUTFILE$", str(mzml.with_suffix("")))
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False
    ) as f:
        f.write(input_file_content)
    subprocess.run(
        [str(mzmine), "-batch", f.name],
        check=True,
        capture_output=True,
    )


def _to_csv(mzmine: Path, machine_data: Path) -> None:
    mzml = _to_mzml(machine_data)
    _mzml_to_csv(mzml, mzmine)


if __name__ == "__main__":
    main()
