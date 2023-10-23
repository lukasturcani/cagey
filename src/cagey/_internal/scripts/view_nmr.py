import argparse
from collections.abc import Iterable
from operator import attrgetter
from pathlib import Path

import polars as pl
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

import cagey
from cagey import NmrAldehydePeak, NmrIminePeak, Reaction


def main() -> None:
    pl.Config.set_tbl_cols(-1)
    pl.Config.set_tbl_rows(-1)
    args = _parse_args()
    engine = create_engine(
        f"sqlite:///{args.database}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    experiment, plate, formulation_number = args.title_file.read_text().split(
        "_"
    )
    with Session(engine) as session:
        reaction_query = select(Reaction).where(
            Reaction.experiment == experiment,
            Reaction.plate == int(plate),
            Reaction.formulation_number == int(formulation_number),
        )
        reaction = session.exec(reaction_query).one()

    nmr_spectrum = cagey.nmr.get_spectrum(args.title_file.parent, reaction)
    aldehyde_peak_df = _get_peak_df(nmr_spectrum.aldehyde_peaks)
    print("aldehyde peaks")
    print(aldehyde_peak_df)
    imine_peak_df = _get_peak_df(nmr_spectrum.imine_peaks)
    print("imine peaks")
    print(imine_peak_df)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("title_file", type=Path)
    return parser.parse_args()


def _get_peak_df(
    peaks: Iterable[NmrAldehydePeak | NmrIminePeak],
) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "ppm": list(map(attrgetter("ppm"), peaks)),
            "amplitude": list(map(attrgetter("amplitude"), peaks)),
        }
    ).sort(["ppm", "amplitude"])


if __name__ == "__main__":
    main()
