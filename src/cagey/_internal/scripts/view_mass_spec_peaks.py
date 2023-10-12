import argparse
from pathlib import Path
from dataclasses import dataclass

from sqlalchemy.orm import aliased
from sqlmodel import Session, select

import cagey
from cagey import Reaction, Precursor


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    reaction_data = ReactionData.from_path(args.mass_spec_csv)
    with Session(engine) as session:
        Di = aliased(Precursor)
        Tri = aliased(Precursor)
        reaction_query = select(Reaction, Di, Tri).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
            Di.name == Reaction.di_name,
            Tri.name == Reaction.tri_name,
        )
        reaction, di, tri = session.exec(reaction_query).one()

    cagey.mass_spec.get_mass_spectrum(args.mass_spec_csv.path, reaction, di, tri)


@dataclass(frozen=True, slots=True)
class ReactionData:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionData":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionData(experiment, int(plate), int(formulation_number))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("mass_spec_csv", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
