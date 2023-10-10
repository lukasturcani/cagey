import argparse
from pathlib import Path

import polars as pl
from sqlmodel import create_engine
from sqlmodel.pool import StaticPool


def main() -> None:
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(-1)
    args = _parse_args()
    old_results = (
        pl.scan_csv(args.csv_results)
        .rename(
            {
                "Plate": "plate",
                "Itensity": "intensity",
                "Adduct": "adduct",
                "Charge": "charge",
                "Topology": "topology",
                "Position": "formulation_number",
                "M/Z Present?": "spectrum_mz",
            }
        )
        .filter(pl.col("Correct_Seperation?"))
    )
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    mass_spectrums = (
        pl.read_database("SELECT * from massspectrum", engine.connect())
        .lazy()
        .rename({"id": "mass_spectrum_id"})
    )
    corrected_peaks = pl.read_database(
        "SELECT * from correctedmassspecpeak", engine.connect()
    ).lazy()
    results = mass_spectrums.join(
        corrected_peaks, on="mass_spectrum_id", how="inner"
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("csv_results", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
