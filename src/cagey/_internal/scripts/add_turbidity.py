import argparse
import json
from pathlib import Path
from typing import TypedDict

from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool
from tqdm import tqdm

import cagey
from cagey import Reaction, Turbidity


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for path in tqdm(args.data, desc="adding turbidity data"):
            data = _read_json(path)
            dissolved_reference = data["turbidity_dissolved_reference"]
            reaction_query = select(Reaction).where(
                Reaction.experiment == data["experiment"],
                Reaction.plate == data["plate"],
                Reaction.formulation_number == data["formulation_number"],
            )
            reaction = session.exec(reaction_query).one()
            session.add(
                Turbidity(
                    reaction_id=reaction.id,
                    state=cagey.turbidity.get_turbid_state(
                        data["turbidity_data"], dissolved_reference
                    ),
                )
            )
        session.commit()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("data", type=Path, nargs="+")
    return parser.parse_args()


class TurbidityData(TypedDict):
    experiment: str
    plate: int
    formulation_number: int
    turbidity_data: dict[str, float]
    turbidity_dissolved_reference: float


def _read_json(path: Path) -> TurbidityData:
    with path.open() as file:
        return json.load(file)
