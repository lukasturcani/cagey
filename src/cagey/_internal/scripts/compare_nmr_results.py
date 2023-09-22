import argparse
from pathlib import Path

import polars as pl
from sqlmodel import create_engine, select
from sqlmodel.pool import StaticPool

from cagey._internal.nmr import NmrSpectrum


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    old_results = pl.read_csv(args.csv_results)
    for row in old_results.rows(named=True):
        nmr_spectrum = select(NmrSpectrum).where(
            NmrSpectrum.experiment == row["Experiment_Name"],
            NmrSpectrum.plate == row["Plate_Name"].replace("PLATE", "P"),
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
