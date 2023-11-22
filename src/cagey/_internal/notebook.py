from dataclasses import dataclass
from operator import attrgetter
from pathlib import Path

import polars as pl
from sqlalchemy.engine import Engine
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from cagey._internal.ms import get_spectrum as _get_ms_spectrum
from cagey._internal.ms import get_topologies
from cagey._internal.nmr import get_spectrum as _get_nmr_spectrum
from cagey._internal.tables import (
    MassSpectrum,
    Precursor,
    Reaction,
    TurbidityDissolvedReference,
)


@dataclass(frozen=True, slots=True)
class ReactionData:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_ms_path(path: Path) -> "ReactionData":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionData(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_nmr_title(path: Path) -> "ReactionData":
        experiment, plate, formulation_number = path.read_text().split("_")
        return ReactionData(experiment, int(plate), int(formulation_number))


def get_ms_spectrum_from_file(  # noqa: PLR0913
    path: Path,
    engine: Engine,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> MassSpectrum:
    reaction_data = ReactionData.from_ms_path(path)
    with Session(engine) as session:
        Di = aliased(Precursor)  # noqa: N806
        Tri = aliased(Precursor)  # noqa: N806
        reaction_query = select(Reaction, Di, Tri).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
            Di.name == Reaction.di_name,
            Tri.name == Reaction.tri_name,
        )
        reaction, di, tri = session.exec(reaction_query).one()
        spectrum = _get_ms_spectrum(
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
        for peak_id, peak in enumerate(spectrum.peaks, 1):
            peak.id = peak_id
    return spectrum


def get_ms_topology_assignments_from_file(  # noqa: PLR0913
    path: Path,
    engine: Engine,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> pl.DataFrame:
    spectrum = get_ms_spectrum_from_file(
        path=path,
        engine=engine,
        calculated_peak_tolerance=calculated_peak_tolerance,
        separation_peak_tolerance=separation_peak_tolerance,
        max_ppm_error=max_ppm_error,
        max_separation=max_separation,
        min_peak_height=min_peak_height,
    )
    topologies = tuple(get_topologies(spectrum))
    assignments = pl.DataFrame(
        {
            "mass_spec_peak_id": list(
                map(attrgetter("mass_spec_peak_id"), topologies)
            ),
            "topology": list(map(attrgetter("topology"), topologies)),
        }
    )
    return assignments.join(
        spectrum.get_peak_df(), on="mass_spec_peak_id", how="left"
    )


def get_ms_topology_assignments_from_database(
    engine: Engine,
) -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, di_name, "
            "       tri_name, adduct, charge, calculated_mz, spectrum_mz, "
            "       separation_mz, intensity, topology "
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
            ppm_error=get_ppm_error(),
            separation=get_separation(),
        )
    )


def get_nmr_aldehyde_peaks_from_database(engine: Engine) -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, di_name, tri_name, "
        "       ppm, amplitude "
        "FROM nmraldehydepeak "
        "LEFT JOIN nmrspectrum "
        "ON nmr_spectrum_id = nmrspectrum.id "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_nmr_imine_peaks_from_database(engine: Engine) -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, di_name, tri_name, "
        "       ppm, amplitude "
        "FROM nmriminepeak "
        "LEFT JOIN nmrspectrum "
        "ON nmr_spectrum_id = nmrspectrum.id "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_reactions_from_database(engine: Engine) -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, "
        "       di_name, di.smiles AS di_smiles, "
        "tri_name, tri.smiles AS tri_smiles "
        "FROM reaction "
        "LEFT JOIN precursor di "
        "ON di.name = reaction.di_name "
        "LEFT JOIN precursor tri "
        "ON tri.name = reaction.tri_name",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_ms_peaks_from_database(engine: Engine) -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, di_name, "
            "       tri_name, adduct, charge, calculated_mz, spectrum_mz, "
            "       separation_mz, intensity "
            "FROM massspecpeak "
            "LEFT JOIN massspectrum "
            "ON mass_spectrum_id = massspectrum.id "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id",
            engine.connect(),
        )
        .sort(["experiment", "plate", "formulation_number"])
        .with_columns(
            ppm_error=get_ppm_error(),
            separation=get_separation(),
        )
    )


def get_nmr_aldehyde_peaks_from_file(
    path: Path,
    engine: Engine,
) -> pl.DataFrame:
    reaction_data = ReactionData.from_nmr_title(path)
    with Session(engine) as session:
        reaction_query = select(Reaction).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
        )
        reaction = session.exec(reaction_query).one()
    spectrum = _get_nmr_spectrum(path.parent, reaction)
    for peak_id, peak in enumerate(spectrum.aldehyde_peaks, 1):
        peak.id = peak_id
    return spectrum.get_aldehyde_peak_df()


def get_nmr_imine_peaks_from_file(
    path: Path,
    engine: Engine,
) -> pl.DataFrame:
    reaction_data = ReactionData.from_nmr_title(path)
    with Session(engine) as session:
        reaction_query = select(Reaction).where(
            Reaction.experiment == reaction_data.experiment,
            Reaction.plate == reaction_data.plate,
            Reaction.formulation_number == reaction_data.formulation_number,
        )
        reaction = session.exec(reaction_query).one()
    spectrum = _get_nmr_spectrum(path.parent, reaction)
    for peak_id, peak in enumerate(spectrum.imine_peaks, 1):
        peak.id = peak_id
    return spectrum.get_imine_peak_df()


def get_ppm_error() -> pl.Expr:
    return (
        (pl.col("calculated_mz") - pl.col("spectrum_mz"))
        / pl.col("calculated_mz")
        * pl.lit(1e6)
    ).abs()


def get_separation() -> pl.Expr:
    return (pl.col("separation_mz") - pl.col("spectrum_mz")) - (
        1 / pl.col("charge")
    )


def get_turbidity_from_database(engine: Engine) -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, state "
        "FROM turbidity "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_turbidity_dissolved_reference_from_database(
    engine: Engine
) -> pl.DataFrame:
    return pl.read_database(
        "SELECT experiment, plate, formulation_number, dissolved_reference "
        "FROM turbiditydissolvedreference "
        "LEFT JOIN reaction "
        "ON reaction_id = reaction.id",
        engine.connect(),
    ).sort(["experiment", "plate", "formulation_number"])


def get_turbidity_measurements_from_database(
    engine: Engine,
) -> pl.DataFrame:
    return (
        pl.read_database(
            "SELECT experiment, plate, formulation_number, time, turbidity "
            "FROM turbiditymeasurement "
            "LEFT JOIN reaction "
            "ON reaction_id = reaction.id ",
            engine.connect(),
        )
        .with_columns(
            pl.col("time").str.strptime(
                pl.Datetime, format="%Y_%m_%d_%H_%M_%S_%f"
            ),
        )
        .sort("time")
    )
