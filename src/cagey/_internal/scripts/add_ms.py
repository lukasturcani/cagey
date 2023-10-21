import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import aliased
from sqlmodel import Session, SQLModel, and_, create_engine, or_, select
from sqlmodel.pool import StaticPool

import cagey
from cagey import Precursor, Reaction

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
    reaction_keys = tuple(map(ReactionKey.from_path, args.csv))
    reaction_query = select(Reaction, Di, Tri).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )

    with Session(engine) as session:
        reactions = {
            ReactionKey.from_reaction(result[0]): result
            for result in session.exec(reaction_query).all()
        }
        for path, reaction_key in zip(args.csv, reaction_keys, strict=True):
            reaction, di, tri = reactions[reaction_key]
            session.add(cagey.ms.get_spectrum(path, reaction, di, tri))
        session.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv", type=Path, nargs="+")
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


if __name__ == "__main__":
    main()
