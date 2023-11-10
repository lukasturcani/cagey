from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import polars as pl
import rdkit.Chem.AllChem as rdkit  # noqa: N813
from pyopenms import EmpiricalFormula

from cagey._internal.tables import (
    MassSpecPeak,
    MassSpecTopologyAssignment,
    MassSpectrum,
    Precursor,
    Reaction,
)

ADDUCTS = (
    EmpiricalFormula("H1"),
    EmpiricalFormula("H2"),
    EmpiricalFormula("H3"),
    EmpiricalFormula("H4"),
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
CHARGE1_BANNED_ADDUCTS = {"H2", "K2", "Na2", "H3", "K3", "Na3", "H4"}
CHARGE2_BANNED_ADDUCTS = {"H1", "H3", "K1", "K3", "Na1", "Na3", "H4"}
CHARGE3_BANNED_ADDUCTS = {"H1", "H2", "Na1", "Na2", "K1", "K2", "H4"}
CHARGE4_BANNED_ADDUCTS = {
    "H1",
    "H2",
    "H3",
    "Na1",
    "Na2",
    "Na3",
    "K1",
    "K2",
    "K3",
}
PRECURSOR_COUNTS = (
    (2, 3),
    (4, 6),
    (3, 5),
    (6, 9),
    (8, 12),
)


def get_spectrum(  # noqa: PLR0913
    path: Path,
    reaction: Reaction,
    di: Precursor,
    tri: Precursor,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
) -> MassSpectrum:
    peaks = (
        pl.scan_csv(path).filter(pl.col("height") > min_peak_height).collect()
    )
    mass_spectrum = MassSpectrum(reaction_id=reaction.id)
    di_formula = _get_precursor_formula(di)
    tri_formula = _get_precursor_formula(tri)
    for adduct, charge, (tri_count, di_count) in product(
        ADDUCTS, CHARGES, PRECURSOR_COUNTS
    ):
        if charge == 1 and str(adduct.toString()) in CHARGE1_BANNED_ADDUCTS:
            continue
        if charge == 2 and str(adduct.toString()) in CHARGE2_BANNED_ADDUCTS:  # noqa: PLR2004
            continue
        if charge == 3 and str(adduct.toString()) in CHARGE3_BANNED_ADDUCTS:  # noqa: PLR2004
            continue
        if charge == 4 and str(adduct.toString()) in CHARGE4_BANNED_ADDUCTS:  # noqa: PLR2004
            continue

        di_data = PrecursorData(di_formula, di_count, 2)
        tri_data = PrecursorData(tri_formula, tri_count, 3)
        cage_mz = _get_cage_mz(di_data, tri_data, adduct, charge)
        cage_peaks = peaks.filter(
            pl.col("mz").is_between(
                cage_mz - calculated_peak_tolerance,
                cage_mz + calculated_peak_tolerance,
            )
        )
        if cage_peaks.is_empty():
            continue
        cage_peak = cage_peaks.row(0, named=True)
        separation_mz = cage_peak["mz"] + H_MONO_WEIGHT / charge
        separation_peaks = peaks.filter(
            pl.col("mz").is_between(
                separation_mz - separation_peak_tolerance,
                separation_mz + separation_peak_tolerance,
            )
        )
        if not separation_peaks.is_empty():
            separation_mz = separation_peaks.row(0, named=True)["mz"]
            ppm_error = abs((cage_mz - cage_peak["mz"]) / cage_mz * 1e6)
            separation = separation_mz - cage_peak["mz"]
            if (
                ppm_error <= max_ppm_error
                and abs(separation - 1 / charge) <= max_separation
            ):
                mass_spectrum.peaks.append(
                    MassSpecPeak(
                        di_count=di_count,
                        tri_count=tri_count,
                        adduct=str(adduct.toString()),
                        charge=charge,
                        calculated_mz=cage_mz,
                        spectrum_mz=cage_peak["mz"],
                        separation_mz=separation_mz,
                        intensity=cage_peak["height"],
                    )
                )
    return mass_spectrum


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


def get_topologies(
    spectrum: MassSpectrum,
) -> Iterator[MassSpecTopologyAssignment]:
    valid_peaks = tuple(
        peak
        for peak in spectrum.peaks
        if (peak.tri_count, peak.di_count) != (3, 5) and peak.charge in {1, 2}
    )

    has_four_plus_six = any(
        peak.tri_count == 4 and peak.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_singly_charged_2_plus_3 = any(
        peak.charge == 1 and peak.tri_count == 2 and peak.di_count == 3  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_doubly_charged_2_plus_3 = any(
        peak.charge == 2 and peak.tri_count == 2 and peak.di_count == 3  # noqa: PLR2004
        for peak in valid_peaks
    )
    avoid_2_plus_3 = (
        has_four_plus_six
        and has_singly_charged_2_plus_3
        and not has_doubly_charged_2_plus_3
    )
    has_eight_plus_twelve = any(
        peak.tri_count == 8 and peak.di_count == 12  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_singly_charged_4_plus_6 = any(
        peak.charge == 1 and peak.tri_count == 4 and peak.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_doubly_charged_4_plus_6 = any(
        peak.charge == 2 and peak.tri_count == 4 and peak.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    avoid_4_plus_6 = (
        has_eight_plus_twelve
        and has_singly_charged_4_plus_6
        and not has_doubly_charged_4_plus_6
    )
    for peak in valid_peaks:
        topology = f"{peak.tri_count}+{peak.di_count}"
        if avoid_2_plus_3 and topology == "2+3":
            continue
        if avoid_4_plus_6 and topology == "4+6":
            continue
        yield MassSpecTopologyAssignment(
            mass_spec_peak_id=peak.id,
            topology=f"{peak.tri_count}+{peak.di_count}",
        )
