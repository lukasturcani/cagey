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
        pl.Config.set_tbl_cols(-1)
    if "nmr" in args.tables:
        nmr_spectra = pl.read_database(
            "SELECT * FROM nmrspectrum", engine.connect()
        )
        print("nmrspectrum")
        print(nmr_spectra)
    if "aldehyde" in args.tables:
        aldehyde_peaks = pl.read_database(
            "SELECT * FROM aldehydepeak", engine.connect()
        )
        print("aldehydepeak")
        print(aldehyde_peaks)
    if "imine" in args.tables:
        imine_peaks = pl.read_database(
            "SELECT * FROM iminepeak", engine.connect()
        )
        print("iminepeak")
        print(imine_peaks)
    if "precursor" in args.tables:
        precursors = pl.read_database(
            "SELECT * FROM precursor", engine.connect()
        )
        print("precursor")
        print(precursors)
    if "reaction" in args.tables:
        reactions = pl.read_database(
            "SELECT * FROM reaction", engine.connect()
        )
        print("reaction")
        print(reactions)
    if "mass_spec" in args.tables:
        mass_spec = pl.read_database(
            "SELECT * FROM massspectrum", engine.connect()
        )
        print("massspectrum")
        print(mass_spec)
    if "corrected_mass_spec_peak" in args.tables:
        corrected_mass_spec_peaks = pl.read_database(
            "SELECT * FROM correctedmassspecpeak", engine.connect()
        )
        print("correctedmassspecpeak")
        print(corrected_mass_spec_peaks)
    if "mass_spec_peak" in args.tables:
        mass_spec_peaks = pl.read_database(
            "SELECT * FROM massspecpeak", engine.connect()
        )
        print("massspecpeak")
        print(mass_spec_peaks)
    if "mass_spec_topology" in args.tables:
        mass_spec_topology_assignments = pl.read_database(
            "SELECT * FROM massspectopologyassignment", engine.connect()
        )
        print("massspectopologyassignment")
        print(mass_spec_topology_assignments)


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
        choices=[
            "nmr",
            "aldehyde",
            "imine",
            "precursor",
            "reaction",
            "mass_spec",
            "corrected_mass_spec_peak",
            "mass_spec_peak",
            "mass_spec_topology",
        ],
        nargs="*",
        default=[
            "nmr",
            "aldehyde",
            "imine",
            "precursor",
            "reaction",
            "mass_spec",
            "corrected_mass_spec_peak",
            "mass_spec_peak",
            "mass_spec_topology",
        ],
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
