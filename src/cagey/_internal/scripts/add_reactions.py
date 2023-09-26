import argparse
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

import cagey


def main() -> None:
    args = _parse_args()

    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        cagey.reactions.add_precursors(session)
        cagey.reactions.add_ab_02_005_data(session)
        cagey.reactions.add_ab_02_007_data(session)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
