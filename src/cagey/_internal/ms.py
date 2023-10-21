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
    Session,
    and_,
    not_,
    or_,
    select,
)

from cagey._internal.tables import (
    MassSpecPeak,
    MassSpecTopologyAssignment,
    MassSpectrum,
    Precursor,
    Reaction,
    SeparationMassSpecPeak,
)

ADDUCTS = (
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
H_MONO_WEIGHT = EmpiricalFormula("H").getMonoWeight()
CHARGES = (1, 2, 3, 4)
CHARGE1_BANNED_ADDUCTS = {"H2", "K2", "Na2", "H3", "K3", "Na3"}
CHARGE2_BANNED_ADDUCTS = {"H1", "H3", "K1", "K3", "Na1", "Na3"}
PRECURSOR_COUNTS = (
    (2, 3),
    (4, 6),
    (3, 5),
    (6, 9),
    (8, 12),
)


def get_spectrum(
    path: Path,
    reaction: Reaction,
    di: Precursor,
    tri: Precursor,
) -> MassSpectrum:
    peaks = pl.scan_csv(path).filter(pl.col("height") > 1e4).collect()
    mass_spectrum = MassSpectrum(reaction_id=reaction.id)
    di_formula = _get_precursor_formula(di)
    tri_formula = _get_precursor_formula(tri)
    for adduct, charge, (tri_count, di_count) in product(
        ADDUCTS, CHARGES, PRECURSOR_COUNTS
    ):
        if charge == 1 and str(adduct.toString()) in CHARGE1_BANNED_ADDUCTS:
            continue
        if charge == 2 and str(adduct.toString()) in CHARGE2_BANNED_ADDUCTS:
            continue

        di_data = PrecursorData(di_formula, di_count, 2)
        tri_data = PrecursorData(tri_formula, tri_count, 3)
        cage_mz = _get_cage_mz(di_data, tri_data, adduct, charge)
        cage_peaks = peaks.filter(
            pl.col("mz").is_between(cage_mz - 0.1, cage_mz + 0.1)
        )
        if cage_peaks.is_empty():
            continue
        cage_peak = cage_peaks.row(0, named=True)
        separation_mz = cage_peak["mz"] + H_MONO_WEIGHT / charge
        separation_peaks = peaks.filter(
            pl.col("mz").is_between(separation_mz - 0.1, separation_mz + 0.1)
        )
        if separation_peaks.is_empty():
            mass_spectrum.peaks.append(
                MassSpecPeak(
                    di_count=di_count,
                    tri_count=tri_count,
                    adduct=str(adduct.toString()),
                    charge=charge,
                    di_name=reaction.di_name,
                    tri_name=reaction.tri_name,
                    calculated_mz=cage_mz,
                    spectrum_mz=cage_peak["mz"],
                    intensity=cage_peak["height"],
                )
            )
        else:
            mass_spectrum.separation_peaks.append(
                SeparationMassSpecPeak(
                    di_count=di_count,
                    tri_count=tri_count,
                    adduct=str(adduct.toString()),
                    charge=charge,
                    di_name=reaction.di_name,
                    tri_name=reaction.tri_name,
                    calculated_mz=cage_mz,
                    spectrum_mz=cage_peak["mz"],
                    separation_mz=separation_peaks.row(0, named=True)["mz"],
                    intensity=cage_peak["height"],
                )
            )
    return mass_spectrum


def add_topology_assignments(
    session: Session,
    commit: bool = True,
) -> None:
    query = select(SeparationMassSpecPeak).where(
        not_(
            and_(
                SeparationMassSpecPeak.tri_count == 3,
                SeparationMassSpecPeak.di_count == 5,
            )
        ),
        or_(
            SeparationMassSpecPeak.charge == 1,
            SeparationMassSpecPeak.charge == 2,
        ),
    )
    session.add_all(_assign_cage_topology(session.exec(query)))

    if commit:
        session.commit()


def _get_precursor_formula(
    precursor: Precursor,
) -> EmpiricalFormula:
    return EmpiricalFormula(
        rdkit.CalcMolFormula(rdkit.MolFromSmiles(precursor.smiles))
    )


@dataclass(frozen=True, slots=True)
class Peak:
    mz: float
    height: float


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionKey":
        experiment, plate_data, _ = path.name.split("_")
        plate, formulation_number_ = plate_data.split("-")
        formulation_number = int(formulation_number_)
        return ReactionKey(
            experiment=experiment,
            plate=int(plate[1:]),
            formulation_number=formulation_number,
        )


@dataclass(frozen=True, slots=True)
class ReactionData:
    path: Path
    reaction: Reaction


@dataclass(frozen=True, slots=True)
class PrecursorData:
    formula: EmpiricalFormula
    count: int
    num_functional_groups: int


def _get_cage_mz(
    di: PrecursorData,
    tri: PrecursorData,
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
    peaks: Iterable[SeparationMassSpecPeak],
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
