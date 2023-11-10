import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy.orm import aliased
from sqlmodel import Session, SQLModel, and_, create_engine, or_, select
from sqlmodel.pool import StaticPool
from tqdm import tqdm

import cagey
from cagey import Precursor, Reaction

Di = aliased(Precursor)
Tri = aliased(Precursor)


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
            ReactionKey.from_reaction(reaction): ReactionData(
                reaction=reaction, di=di, tri=tri
            )
            for reaction, di, tri in session.exec(reaction_query).all()
        }
        spectrums = []
        for csv in tqdm(args.csv, desc="adding mass spectra"):
            reaction_data = reactions[ReactionKey.from_path(csv)]
            spectrum = cagey.ms.get_spectrum(
                csv,
                reaction_data.reaction,
                reaction_data.di,
                reaction_data.tri,
            )
            spectrums.append(spectrum)
        session.add_all(spectrums)
        session.commit()
        for spectrum in tqdm(spectrums, desc="adding topology assignments"):
            session.add_all(cagey.ms.get_topologies(spectrum))
        session.commit()


def _get_reaction_query(reaction_key: ReactionKey) -> Any:
    return and_(
        Reaction.experiment == reaction_key.experiment,
        Reaction.plate == reaction_key.plate,
        Reaction.formulation_number == reaction_key.formulation_number,
        Di.name == Reaction.di_name,
        Tri.name == Reaction.tri_name,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv", type=Path, nargs="+")
    return parser.parse_args()
