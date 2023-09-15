from collections.abc import Iterator
from pathlib import Path

import cagey
import polars as pl
from pytest import fixture
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


def test_nmr_extraction(engine: Engine) -> None:
    with Session(engine) as session:
        cagey.nmr.add_data(Path("/home/lukas/downloads/NMR_data"), session)
        df = pl.read_database("SELECT * FROM aldehydepeak", engine.connect())
        print(df)
        assert False


@fixture
def engine() -> Engine:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine
