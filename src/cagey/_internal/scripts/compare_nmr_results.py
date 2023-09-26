import argparse
from pathlib import Path

import polars as pl
from sqlmodel import Session, create_engine, select
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
    missing = 0
    not_missing = 0
    with Session(engine) as session:
        for row in old_results.rows(named=True):
            plate = (
                "P4"
                if "PLATE2B" in row["Plate_Name"]
                else row["Plate_Name"].replace("PLATE", "P")
            )
            statement = select(NmrSpectrum).where(
                NmrSpectrum.experiment == row["Experiment_Name"],
                NmrSpectrum.plate == plate,
                NmrSpectrum.formulation_number == row["Formulation_Number"],
            )
            nmr_spectrum = session.exec(statement).one_or_none()
            if nmr_spectrum is None:
                print(
                    row["Experiment_Name"],
                    row["Plate_Name"],
                    row["Formulation_Number"],
                )
                missing += 1
                continue
            not_missing += 1
            has_imine = len(nmr_spectrum.imine_peaks) > 0
            assert row["Comp_Imine_Check"] == has_imine
            has_aldehyde = len(nmr_spectrum.aldehyde_peaks) > 0
            assert row["Comp_Aldehyde_Check"] == has_aldehyde
    print(f"Missing: {missing}")
    print(f"Not missing: {not_missing}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
