import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
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


def add_data(
    mass_spec_path: Path,
    session: Session,
    commit: bool = True,
) -> None:
    adducts = (
        EmpiricalFormula("H"),
        EmpiricalFormula("H2"),
        EmpiricalFormula("H3"),
        EmpiricalFormula("K"),
        EmpiricalFormula("Na"),
        EmpiricalFormula("NH4"),
    )
    charges = (1, 2, 3, 4)
    precursor_counts = (
        (2, 3),
        (4, 6),
        (3, 5),
        (6, 9),
        (8, 12),
    )
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
            di = Precursor(di_formula, di_count, 2)
            tri = Precursor(tri_formula, tri_count, 3)
            cage_weight = _get_cage_weight(di, tri, adduct, charge)
            cage_peaks = peaks.filter(
                pl.col("mz").is_between(cage_weight - 0.1, cage_weight + 0.1)
            )
            if cage_peaks.is_empty():
                continue
            cage_peak = cage_peaks.row(0, named=True)
            corrected_weight = cage_peak["mz"] + h_mono_weight / charge
            corrected_peaks = peaks.filter(
                pl.col("mz").is_between(
                    corrected_weight - 0.1, corrected_weight + 0.1
                )
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
                        calculated_mz=cage_weight,
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
                        calculated_mz=cage_weight,
                        spectrum_mz=cage_peak["mz"],
                        corrected_mz=corrected_peaks.row(0, named=True)["mz"],
                        intensity=cage_peak["height"],
                    )
                )
        session.add(mass_spectrum)

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


def _get_cage_weight(
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


def _get_cage_formula(
    di: Precursor,
    tri: Precursor,
) -> str:
    water = EmpiricalFormula("H2O")
    num_imine_bonds = min(
        di.count * di.num_functional_groups,
        tri.count * tri.num_functional_groups,
    )
    formula = EmpiricalFormula("")
    for _ in range(di.count):
        formula += di.formula
    for _ in range(tri.count):
        formula += tri.formula
    for _ in range(num_imine_bonds):
        formula -= water
    return str(formula.toString())
