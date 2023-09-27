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
        cagey.mass_spec.add_data(args.mass_spec_directory, session)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("mass_spec_directory", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
