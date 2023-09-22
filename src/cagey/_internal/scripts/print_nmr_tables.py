import argparse
from pathlib import Path

import polars as pl
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool


def main() -> None:
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if args.verbose:
        pl.Config.set_tbl_rows(-1)
    if "nmr" in args.tables:
        nmr_specta = pl.read_database(
            "SELECT * FROM nmrspectrum", engine.connect()
        )
        print(nmr_specta)
    if "aldehyde" in args.tables:
        aldehyde_peaks = pl.read_database(
            "SELECT * FROM aldehydepeak", engine.connect()
        )
        print(aldehyde_peaks)
    if "imine" in args.tables:
        imine_peaks = pl.read_database(
            "SELECT * FROM iminepeak", engine.connect()
        )
        print(imine_peaks)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path, help="the database file")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print the full dataframe",
    )
    parser.add_argument(
        "-t",
        "--tables",
        choices=["nmr", "aldehyde", "imine"],
        nargs="*",
        default=["nmr", "aldehyde", "imine"],
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
