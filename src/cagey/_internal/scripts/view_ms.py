import argparse
from dataclasses import dataclass
from pathlib import Path

import polars as pl
from sqlalchemy.orm import aliased
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

import cagey
from cagey import Precursor, Reaction


def main() -> None:
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(-1)
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    reaction_data = ReactionData.from_path(args.csv)
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

    peak_df = cagey.ms.get_spectrum(args.csv, reaction, di, tri).to_df()
    print(peak_df)


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
    parser.add_argument("csv", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
