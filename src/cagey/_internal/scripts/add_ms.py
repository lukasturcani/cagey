import argparse
import pkgutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from sqlalchemy.orm import aliased
from sqlmodel import Session, SQLModel, and_, create_engine, or_, select
from sqlmodel.pool import StaticPool
from tqdm import tqdm

import cagey
from cagey import MassSpectrum, Precursor, Reaction

Di = aliased(Precursor)
Tri = aliased(Precursor)


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    reaction_keys = tuple(map(ReactionKey.from_path, args.machine_data))
    reaction_query = select(Reaction, Di, Tri).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )

    with Session(engine) as session:
        reactions = {
            ReactionKey.from_reaction(reaction): ReactionData(
                reaction=reaction, di=di, tri=tri
            )
            for reaction, di, tri in session.exec(reaction_query).all()
        }
        get_mass_spectrum = partial(_get_mass_spectrum, args.mzmine)
        with Pool() as pool:
            failures = []
            spectrums = []
            for result in tqdm(
                pool.imap_unordered(
                    get_mass_spectrum,
                    map(
                        partial(_get_mass_spectrum_input, reactions),
                        args.machine_data,
                    ),
                ),
                desc="adding mass spectra",
                total=len(args.machine_data),
            ):
                match result:
                    case MassSpectrum():
                        spectrums.append(result)
                    case Path():
                        failures.append(result)
        if failures:
            failures_repr = ",\n\t".join(map(str, failures))
            print(f"failed to process: [\n\t{failures_repr},\n]")
        session.add_all(spectrums)
        session.commit()
        for spectrum in tqdm(spectrums, desc="adding topology assignments"):
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


@dataclass(frozen=True, slots=True)
class ReactionData:
    reaction: Reaction
    di: Precursor
    tri: Precursor


def _get_mass_spectrum_input(
    reactions: dict[ReactionKey, ReactionData],
    machine_data: Path,
) -> tuple[ReactionData, Path]:
    reaction_key = ReactionKey.from_path(machine_data)
    return reactions[reaction_key], machine_data


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


def _mzml_to_csv(mzml: Path, mzmine: Path) -> Path:
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
    return mzml.with_suffix(".csv")


def _get_mass_spectrum(
    mzmine: Path,
    input: tuple[ReactionData, Path],
) -> MassSpectrum | Path:
    try:
        reaction_data, machine_data = input
        mzml = _to_mzml(machine_data)
        csv = _mzml_to_csv(mzml, mzmine)
        return cagey.ms.get_spectrum(
            csv, reaction_data.reaction, reaction_data.di, reaction_data.tri
        )
    except Exception:
        return machine_data


if __name__ == "__main__":
    main()
