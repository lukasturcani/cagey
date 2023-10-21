import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path

import polars as pl
from sqlalchemy.orm import aliased
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

import cagey
from cagey import MassSpecPeak, Precursor, Reaction, SeparationMassSpecPeak


def main() -> None:
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(-1)
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    reaction_data = ReactionData.from_path(args.mass_spec_csv)
    with Session(engine) as session:
        Di = aliased(Precursor)
        Tri = aliased(Precursor)
        reaction_query = select(Reaction, Di, Tri).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
            Di.name == Reaction.di_name,
            Tri.name == Reaction.tri_name,
        )
        reaction, di, tri = session.exec(reaction_query).one()

    mass_spectrum = cagey.ms.get_spectrum(
        args.mass_spec_csv, reaction, di, tri
    )
    peak_df = _get_peak_df(mass_spectrum.peaks)
    print(peak_df)
    corrected_peak_df = _get_separation_peak_df(mass_spectrum.separation_peaks)
    print(corrected_peak_df)


@dataclass(frozen=True, slots=True)
class ReactionData:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionData":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionData(experiment, int(plate), int(formulation_number))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("mass_spec_csv", type=Path)
    return parser.parse_args()


def _get_peak_df(peaks: Sequence[MassSpecPeak]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "di_count": list(map(attrgetter("di_count"), peaks)),
            "tri_count": list(map(attrgetter("tri_count"), peaks)),
            "adduct": list(map(attrgetter("adduct"), peaks)),
            "charge": list(map(attrgetter("charge"), peaks)),
            "di_name": list(map(attrgetter("di_name"), peaks)),
            "tri_name": list(map(attrgetter("tri_name"), peaks)),
            "calculated_mz": list(map(attrgetter("calculated_mz"), peaks)),
            "spectrum_mz": list(map(attrgetter("spectrum_mz"), peaks)),
            "intensity": list(map(attrgetter("intensity"), peaks)),
        }
    )


def _get_separation_peak_df(
    peaks: Sequence[SeparationMassSpecPeak],
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "di_count": list(map(attrgetter("di_count"), peaks)),
            "tri_count": list(map(attrgetter("tri_count"), peaks)),
            "adduct": list(map(attrgetter("adduct"), peaks)),
            "charge": list(map(attrgetter("charge"), peaks)),
            "di_name": list(map(attrgetter("di_name"), peaks)),
            "tri_name": list(map(attrgetter("tri_name"), peaks)),
            "calculated_mz": list(map(attrgetter("calculated_mz"), peaks)),
            "spectrum_mz": list(map(attrgetter("spectrum_mz"), peaks)),
            "separation_mz": list(map(attrgetter("separation_mz"), peaks)),
            "intensity": list(map(attrgetter("intensity"), peaks)),
        }
    )


if __name__ == "__main__":
    main()
