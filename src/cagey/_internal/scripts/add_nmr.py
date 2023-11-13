import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlmodel import Session, SQLModel, and_, create_engine, or_, select
from sqlmodel.pool import StaticPool
from tqdm import tqdm

import cagey
from cagey import Reaction


def main() -> None:
    args = _parse_args()

    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    reaction_keys = tuple(map(ReactionKey.from_title_file, args.title_file))
    reaction_query = select(Reaction).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )
    with Session(engine) as session:
        reactions = {
            ReactionKey.from_reaction(reaction): reaction
            for reaction in session.exec(reaction_query).all()
        }
        for path, reaction_key in tqdm(
            zip(args.title_file, reaction_keys, strict=True),
            desc="adding nmr spectra",
            total=len(args.title_file),
        ):
            reaction = reactions[reaction_key]
            session.add(cagey.nmr.get_spectrum(path.parent, reaction))
        session.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("title_file", type=Path, nargs="+")
    return parser.parse_args()


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_title_file(title_file: Path) -> "ReactionKey":
        title = title_file.read_text()
        experiment, plate, formulation_number = title.split("_")
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
    )


if __name__ == "__main__":
    main()
