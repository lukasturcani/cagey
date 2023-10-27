from dataclasses import dataclass
from pathlib import Path

import polars as pl
from sqlalchemy.engine import Engine
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from cagey._internal.ms import get_spectrum as _get_ms_spectrum
from cagey._internal.tables import MassSpectrum, Precursor, Reaction


@dataclass(frozen=True, slots=True)
class ReactionData:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_ms_path(path: Path) -> "ReactionData":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionData(experiment, int(plate), int(formulation_number))


def get_ms_spectrum(
    path: Path,
    engine: Engine,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> MassSpectrum:
    reaction_data = ReactionData.from_ms_path(path)
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
        return _get_ms_spectrum(
            path=path,
            reaction=reaction,
            di=di,
            tri=tri,
            calculated_peak_tolerance=calculated_peak_tolerance,
            separation_peak_tolerance=separation_peak_tolerance,
            max_ppm_error=max_ppm_error,
            max_separation=max_separation,
            min_peak_height=min_peak_height,
        )


def get_ms_topology_assignments(engine: Engine) -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, di_name, "
            "       tri_name, adduct, charge, calculated_mz, spectrum_mz, "
            "       separation_mz, topology "
            "FROM massspectopologyassignment "
            "LEFT JOIN massspecpeak "
            "ON mass_spec_peak_id = massspecpeak.id "
            "LEFT JOIN massspectrum "
            "ON mass_spectrum_id = massspectrum.id "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id",
            engine.connect(),
        )
        .sort(["experiment", "plate", "formulation_number"])
        .with_columns(
            ppm_error=(
                (pl.col("calculated_mz") - pl.col("spectrum_mz"))
                / pl.col("calculated_mz")
                * pl.lit(1e6)
            ).abs(),
            separation=(pl.col("separation_mz") - pl.col("spectrum_mz"))
            - (1 / pl.col("charge")),
        )
    )
