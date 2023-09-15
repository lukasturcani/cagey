from pathlib import Path

import cagey
import polars as pl
from pytest import fixture
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


def test_nmr_extraction(engine: Engine, datadir: Path) -> None:
    with Session(engine) as session:
        cagey.nmr.add_data(datadir / "NMR_data", session)
        aldehyde_peaks = pl.read_database(
            "SELECT * FROM aldehydepeak", engine.connect()
        )
        assert len(aldehyde_peaks) == 3
        imine_peaks = pl.read_database(
            "SELECT * FROM iminepeak", engine.connect()
        )
        assert len(imine_peaks) == 35


@fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine
