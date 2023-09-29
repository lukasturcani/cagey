import logging
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any

import polars as pl
import rdkit.Chem.AllChem as rdkit
from pyopenms import EmpiricalFormula
from sqlmodel import (
    Field,
    Relationship,
    Session,
    SQLModel,
    UniqueConstraint,
    and_,
    not_,
    or_,
    select,
)

from cagey._internal.reactions import Precursor as PrecursorTable
from cagey._internal.reactions import Reaction

logger = logging.getLogger(__name__)


class MassSpectrum(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("experiment", "plate", "formulation_number"),
    )
    id: int | None = Field(default=None, primary_key=True)
    experiment: str
    plate: str
    formulation_number: int

    corrected_peaks: list["CorrectedMassSpecPeak"] = Relationship(
        back_populates="mass_spectrum"
    )
    peaks: list["MassSpecPeak"] = Relationship(back_populates="mass_spectrum")


class CorrectedMassSpecPeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mass_spectrum_id: int = Field(foreign_key="massspectrum.id")
    di_count: int
    tri_count: int
    adduct: str
    charge: int
    di_name: str = Field(foreign_key="precursor.name")
    tri_name: str = Field(foreign_key="precursor.name")
    calculated_mz: float
    spectrum_mz: float
    corrected_mz: float
    intensity: float

    mass_spectrum: MassSpectrum = Relationship(
        back_populates="corrected_peaks",
    )

    def get_ppm_error(self) -> float:
        return abs(
            (self.calculated_mz - self.spectrum_mz) / self.calculated_mz * 1e6
        )

    def get_separation(self) -> float:
        return self.corrected_mz - self.spectrum_mz


class MassSpecPeak(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mass_spectrum_id: int = Field(foreign_key="massspectrum.id")
    di_count: int
    tri_count: int
    adduct: str
    charge: int
    di_name: str = Field(foreign_key="precursor.name")
    tri_name: str = Field(foreign_key="precursor.name")
    calculated_mz: float
    spectrum_mz: float
    intensity: float

    mass_spectrum: MassSpectrum = Relationship(
        back_populates="peaks",
    )


class MassSpecTopologyAssignment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    mass_spec_peak_id: int = Field(foreign_key="massspecpeak.id")
    topology: str


def add_data(
    mass_spec_path: Path,
    session: Session,
    commit: bool = True,
) -> None:
    adducts = (
        EmpiricalFormula("H1"),
        EmpiricalFormula("H2"),
        EmpiricalFormula("H3"),
        EmpiricalFormula("H3"),
        EmpiricalFormula("K1"),
        EmpiricalFormula("K2"),
        EmpiricalFormula("K3"),
        EmpiricalFormula("Na1"),
        EmpiricalFormula("Na2"),
        EmpiricalFormula("Na3"),
        EmpiricalFormula("N1H4"),
    )
    charges = (1, 2, 3, 4)
    precursor_counts = (
        (2, 3),
        (4, 6),
        (3, 5),
        (6, 9),
        (8, 12),
    )
    charge1_banned_adducts = {"H2", "K2", "Na2", "H3", "K3", "Na3"}
    charge2_banned_adducts = {"H1", "H3", "K1", "K3", "Na1", "Na3"}
    h_mono_weight = EmpiricalFormula("H").getMonoWeight()
    paths = tuple(mass_spec_path.glob("**/*_Processed.csv"))
    query = select(Reaction).where(or_(*map(_get_reaction_filter, paths)))
    reactions = session.exec(query).all()
    for reaction_data in _get_reaction_data(paths, reactions):
        try:
            peaks = pl.read_csv(reaction_data.path).filter(
                pl.col("height") > 1e4
            )
        except pl.NoDataError:
            logger.error("%s is empty", reaction_data.path)
            continue

        mass_spectrum = MassSpectrum(
            experiment=reaction_data.reaction.experiment,
            plate=reaction_data.reaction.plate,
            formulation_number=reaction_data.reaction.formulation_number,
        )

        di_formula = _get_precursor_formula(
            session, reaction_data.reaction.di_name
        )
        tri_formula = _get_precursor_formula(
            session, reaction_data.reaction.tri_name
        )
        for adduct, charge, (di_count, tri_count) in product(
            adducts, charges, precursor_counts
        ):
            if (
                charge == 1
                and str(adduct.toString()) in charge1_banned_adducts
            ):
                continue
            if (
                charge == 2
                and str(adduct.toString()) in charge2_banned_adducts
            ):
                continue

            di = Precursor(di_formula, di_count, 2)
            tri = Precursor(tri_formula, tri_count, 3)
            cage_mz = _get_cage_mz(di, tri, adduct, charge)
            cage_peaks = peaks.filter(
                pl.col("mz").is_between(cage_mz - 0.1, cage_mz + 0.1)
            )
            if cage_peaks.is_empty():
                continue
            cage_peak = cage_peaks.row(0, named=True)
            corrected_mz = cage_peak["mz"] + h_mono_weight / charge
            corrected_peaks = peaks.filter(
                pl.col("mz").is_between(corrected_mz - 0.1, corrected_mz + 0.1)
            )
            if corrected_peaks.is_empty():
                mass_spectrum.peaks.append(
                    MassSpecPeak(
                        di_count=di_count,
                        tri_count=tri_count,
                        adduct=str(adduct.toString()),
                        charge=charge,
                        di_name=reaction_data.reaction.di_name,
                        tri_name=reaction_data.reaction.tri_name,
                        calculated_mz=cage_mz,
                        spectrum_mz=cage_peak["mz"],
                        intensity=cage_peak["height"],
                    )
                )
            else:
                mass_spectrum.corrected_peaks.append(
                    CorrectedMassSpecPeak(
                        di_count=di_count,
                        tri_count=tri_count,
                        adduct=str(adduct.toString()),
                        charge=charge,
                        di_name=reaction_data.reaction.di_name,
                        tri_name=reaction_data.reaction.tri_name,
                        calculated_mz=cage_mz,
                        spectrum_mz=cage_peak["mz"],
                        corrected_mz=corrected_peaks.row(0, named=True)["mz"],
                        intensity=cage_peak["height"],
                    )
                )
        session.add(mass_spectrum)

    if commit:
        session.commit()


def add_topology_assignments(
    session: Session,
    commit: bool = True,
) -> None:
    query = select(CorrectedMassSpecPeak).where(
        not_(
            and_(
                CorrectedMassSpecPeak.tri_count == 3,
                CorrectedMassSpecPeak.di_count == 5,
            )
        ),
        or_(
            CorrectedMassSpecPeak.charge == 1,
            CorrectedMassSpecPeak.charge == 2,
        ),
    )
    session.add_all(_assign_cage_topology(session.exec(query)))

    if commit:
        session.commit()


def _get_precursor_formula(
    session: Session, precursor_name: str
) -> EmpiricalFormula:
    smiles = next(
        session.exec(
            select(PrecursorTable).where(PrecursorTable.name == precursor_name)
        )
    ).smiles
    return EmpiricalFormula(rdkit.CalcMolFormula(rdkit.MolFromSmiles(smiles)))


def _get_reaction_filter(path: Path) -> Any:
    key = ReactionKey.from_path(path)
    return and_(
        Reaction.experiment == key.experiment,
        Reaction.plate == key.plate,
        Reaction.formulation_number == key.formulation_number,
    )


@dataclass(frozen=True, slots=True)
class Peak:
    mz: float
    height: float


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: str
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionKey":
        experiment, plate_data, _ = path.name.split("_")
        plate, formulation_number_ = plate_data.split("-")
        formulation_number = int(formulation_number_)
        return ReactionKey(
            experiment=experiment,
            plate=plate,
            formulation_number=formulation_number,
        )


@dataclass(frozen=True, slots=True)
class ReactionData:
    path: Path
    reaction: Reaction


def _get_reaction_data(
    paths: Iterable[Path],
    reactions: Iterable[Reaction],
) -> Iterator[ReactionData]:
    key_to_path = {ReactionKey.from_path(path): path for path in paths}
    for reaction in reactions:
        key = ReactionKey(
            reaction.experiment, reaction.plate, reaction.formulation_number
        )
        yield ReactionData(path=key_to_path[key], reaction=reaction)


@dataclass(frozen=True, slots=True)
class Precursor:
    formula: EmpiricalFormula
    count: int
    num_functional_groups: int


def _get_cage_mz(
    di: Precursor,
    tri: Precursor,
    adduct: EmpiricalFormula,
    charge: int,
) -> float:
    water = EmpiricalFormula("H2O")
    num_imine_bonds = min(
        di.count * di.num_functional_groups,
        tri.count * tri.num_functional_groups,
    )
    cage_weight = (
        di.formula.getMonoWeight() * di.count
        + tri.formula.getMonoWeight() * tri.count
        - water.getMonoWeight() * num_imine_bonds
        + adduct.getMonoWeight()
    )
    return cage_weight / charge


@dataclass(slots=True)
class PossibleAssignments:
    topologies: list[MassSpecTopologyAssignment] = field(default_factory=list)
    has_four_plus_six: bool = False
    has_single_charged_2_plus_3: bool = False
    has_double_charged_2_plus_3: bool = False


def _assign_cage_topology(
    peaks: Iterable[CorrectedMassSpecPeak],
) -> Iterator[MassSpecTopologyAssignment]:
    possible_assignmnets: dict[ReactionKey, PossibleAssignments] = defaultdict(
        PossibleAssignments
    )
    for peak in filter(
        lambda peak: (
            peak.get_ppm_error() < 10
            and abs(peak.get_separation() - 1 / peak.charge) < 0.02
        ),
        peaks,
    ):
        reaction_key = ReactionKey(
            experiment=peak.mass_spectrum.experiment,
            plate=peak.mass_spectrum.plate,
            formulation_number=peak.mass_spectrum.formulation_number,
        )
        possible_assignment = possible_assignmnets[reaction_key]

        topology = f"{peak.tri_count}+{peak.di_count}"
        if topology == "4+6":
            possible_assignment.has_four_plus_six = True
        if topology == "2+3" and peak.charge == 1:
            possible_assignment.has_single_charged_2_plus_3 = True
        if topology == "2+3" and peak.charge == 2:
            possible_assignment.has_double_charged_2_plus_3 = True

        possible_assignment.topologies.append(
            MassSpecTopologyAssignment(
                mass_spec_peak_id=peak.id,
                topology=topology,
            )
        )

    for assignment in possible_assignmnets.values():
        topologies: Iterable[MassSpecTopologyAssignment]
        topologies = assignment.topologies
        if (
            assignment.has_four_plus_six
            and assignment.has_single_charged_2_plus_3
            and not assignment.has_double_charged_2_plus_3
        ):
            topologies = filter(
                lambda topology: topology.topology != "2+3",
                topologies,
            )
            continue
        yield from topologies
