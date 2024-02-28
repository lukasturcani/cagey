import pkgutil
import subprocess
import tempfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import polars as pl
import rdkit.Chem.AllChem as rdkit  # noqa: N813
from pyopenms import EmpiricalFormula

from cagey._internal.queries import (
    MassSpectrumPeak,
    MassSpectrumTopologyAssignment,
    Row,
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
CHARGE1_BANNED_ADDUCTS = {
    str(EmpiricalFormula(x).toString())
    for x in [
        "H2",
        "K2",
        "Na2",
        "H3",
        "K3",
        "Na3",
        "H4",
    ]
}
CHARGE2_BANNED_ADDUCTS = {
    str(EmpiricalFormula(x).toString())
    for x in [
        "H1",
        "H3",
        "K1",
        "K3",
        "Na1",
        "Na3",
        "H4",
        "N1H4",
    ]
}
CHARGE3_BANNED_ADDUCTS = {
    str(EmpiricalFormula(x).toString())
    for x in [
        "H1",
        "H2",
        "Na1",
        "Na2",
        "K1",
        "K2",
        "H4",
    ]
}
CHARGE4_BANNED_ADDUCTS = {
    str(EmpiricalFormula(x).toString())
    for x in [
        "H1",
        "H2",
        "H3",
        "Na1",
        "Na2",
        "Na3",
        "K1",
        "K2",
        "K3",
    ]
}
PRECURSOR_COUNTS = (
    (2, 3),
    (4, 6),
    (3, 5),
    (6, 9),
    (8, 12),
)


def get_peaks(  # noqa: PLR0913
    path: Path,
    di_smiles: str,
    tri_smiles: str,
    *,
    calculated_peak_tolerance: float = 0.1,
    separation_peak_tolerance: float = 0.1,
    max_ppm_error: float = 10,
    max_separation: float = 0.02,
    min_peak_height: float = 1e4,
    max_between_peak_height: float = 0.7,
) -> Iterator[MassSpectrumPeak]:
    """Yield the peaks of a mass spectrum.

    Parameters:
        path: The path to the mass spectrum csv file.
        di_smiles: The smiles string of the di-topic precursor.
        tri_smiles: The smiles string of the tri-topic precursor.
        calculated_peak_tolerance:
            The delta to the predicted cage m/z in which the cage
            peaks are found.
        separation_peak_tolerance:
            The delta to the predicted separation peak m/z
            in which the separation peaks are found.
        max_ppm_error:
            The maximum allowed error in ppm between the calculated and
            observed cage m/z.
        max_separation:
            The maximum allowed error in the separation between the cage
            and separation peaks.
        min_peak_height: The minimum peak height allowed.
        max_between_peak_height:
            The maximum allowed height for peaks between the cage and
            separation peaks.

    Yields:
        A mass spectrum peak.
    """
    peaks = (
        pl.scan_csv(path).filter(pl.col("height") > min_peak_height).collect()
    )
    di_formula = _get_precursor_formula(di_smiles)
    tri_formula = _get_precursor_formula(tri_smiles)
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
            separation_peak = separation_peaks.row(0, named=True)
            separation_mz = separation_peak["mz"]
            ppm_error = abs((cage_mz - cage_peak["mz"]) / cage_mz * 1e6)
            separation = separation_mz - cage_peak["mz"]
            between_peaks = peaks.filter(
                pl.col("mz").is_between(
                    cage_peak["mz"],
                    separation_mz,
                    closed="none",
                )
                & pl.col("height").gt(
                    separation_peak["height"] * max_between_peak_height
                )
            )
            if (
                ppm_error <= max_ppm_error
                and abs(separation - 1 / charge) <= max_separation
                and between_peaks.is_empty()
            ):
                yield MassSpectrumPeak(
                    di_count=di_count,
                    tri_count=tri_count,
                    adduct=str(adduct.toString()),
                    charge=charge,
                    calculated_mz=cage_mz,
                    spectrum_mz=cage_peak["mz"],
                    separation_mz=separation_mz,
                    intensity=cage_peak["height"],
                )


def _get_precursor_formula(smiles: str) -> EmpiricalFormula:
    return EmpiricalFormula(rdkit.CalcMolFormula(rdkit.MolFromSmiles(smiles)))


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
    peaks: Iterable[Row[MassSpectrumPeak]],
) -> Iterator[MassSpectrumTopologyAssignment]:
    """Yield the topology assignments for the peaks.

    Parameters:
        peaks: The peaks to assign topologies to.

    Yields:
        A topology assignment.
    """
    valid_peaks = tuple(
        peak
        for peak in peaks
        if (peak.item.tri_count, peak.item.di_count) != (3, 5)
        and peak.item.charge in {1, 2}
    )

    has_four_plus_six = any(
        peak.item.tri_count == 4 and peak.item.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_singly_charged_2_plus_3 = any(
        peak.item.charge == 1
        and peak.item.tri_count == 2  # noqa: PLR2004
        and peak.item.di_count == 3  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_doubly_charged_2_plus_3 = any(
        peak.item.charge == 2  # noqa: PLR2004
        and peak.item.tri_count == 2  # noqa: PLR2004
        and peak.item.di_count == 3  # noqa: PLR2004
        for peak in valid_peaks
    )
    avoid_2_plus_3 = (
        has_four_plus_six
        and has_singly_charged_2_plus_3
        and not has_doubly_charged_2_plus_3
    )
    has_eight_plus_twelve = any(
        peak.item.tri_count == 8 and peak.item.di_count == 12  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_singly_charged_4_plus_6 = any(
        peak.item.charge == 1
        and peak.item.tri_count == 4  # noqa: PLR2004
        and peak.item.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    has_doubly_charged_4_plus_6 = any(
        peak.item.charge == 2  # noqa: PLR2004
        and peak.item.tri_count == 4  # noqa: PLR2004
        and peak.item.di_count == 6  # noqa: PLR2004
        for peak in valid_peaks
    )
    avoid_4_plus_6 = (
        has_eight_plus_twelve
        and has_singly_charged_4_plus_6
        and not has_doubly_charged_4_plus_6
    )
    for peak in valid_peaks:
        topology = f"{peak.item.tri_count}+{peak.item.di_count}"
        if avoid_2_plus_3 and topology == "2+3":
            continue
        if avoid_4_plus_6 and topology == "4+6":
            continue
        yield MassSpectrumTopologyAssignment(
            mass_spectrum_peak_id=peak.id,
            topology=f"{peak.item.tri_count}+{peak.item.di_count}",
        )


def machine_data_to_mzml(
    machine_data: Path,
) -> Path:
    """Convert the machine data to mzML.

    Parameters:
        machine_data: The path to the machine data.

    Returns:
        The path to the mzML file.
    """
    subprocess.run(
        [  # noqa: S603, S607
            "docker",
            "run",
            "--rm",
            "--env",
            "WINEDEBUG=-all",
            "--volume",
            f"{machine_data.resolve().parent}:/data",
            "chambm/pwiz-skyline-i-agree-to-the-vendor-licenses",
            "wine",
            "msconvert",
            str(machine_data.name),
            "-o",
            ".",
        ],
        check=True,
        capture_output=True,
    )
    return machine_data.parent / f"{machine_data.stem}.mzML"


def mzml_to_csv(mzml: Path, mzmine: Path) -> Path:
    """Convert the mzML file to a csv file.

    Parameters:
        mzml: The path to the mzML file.
        mzmine: The path to the MZmine version 3.4.

    Returns:
        The path to the csv file.
    """
    mzml = mzml.resolve()
    template = pkgutil.get_data(
        "cagey", "_internal/scripts/mzmine_input_template.xml"
    )
    if template is None:
        msg = "failed to load mzmine input template"
        raise RuntimeError(msg)
    input_file_content = (
        template.decode()
        .replace("$INFILE$", str(mzml))
        .replace("$OUTFILE$", str(mzml.with_suffix("")))
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".xml", delete=False
    ) as f:
        f.write(input_file_content)
    subprocess.run(
        [str(mzmine), "-batch", f.name],  # noqa: S603
        check=True,
        capture_output=True,
    )
    return mzml.with_suffix(".csv")
