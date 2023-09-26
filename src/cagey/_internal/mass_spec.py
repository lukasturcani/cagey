from dataclasses import dataclass

import rdkit.Chem.AllChem as rdkit
from pyopenms import EmpiricalFormula
from sqlmodel import Session


def add_data(session: Session, commit: bool = True) -> None:
    adducts = (
        EmpiricalFormula("H"),
        EmpiricalFormula("H2"),
        EmpiricalFormula("H3"),
        EmpiricalFormula("K"),
        EmpiricalFormula("Na"),
        EmpiricalFormula("NH4"),
    )
    charges = (1, 2, 3, 4)

    if commit:
        session.commit()


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
    num_imine_bonds = di.count * di.num_functional_groups
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
) -> EmpiricalFormula:
    water = EmpiricalFormula("H2O")
    num_imine_bonds = di.count * di.num_functional_groups
    formula = EmpiricalFormula("")
    for _ in range(di.count):
        formula += di.formula
    for _ in range(tri.count):
        formula += tri.formula
    for _ in range(num_imine_bonds):
        formula -= water
    return formula
