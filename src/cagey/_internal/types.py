import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Generic, NewType, TypeVar


@dataclass(frozen=True, slots=True)
class ReactionKey:
    """A unique identifier for a reaction.

    Parameters:
        experiment: The name of the experiment.
        plate: The plate number.
        formulation_number: The formulation number.
    """

    experiment: str
    """The name of the experiment."""
    plate: int
    """The plate number."""
    formulation_number: int
    """The formulation number."""

    @staticmethod
    def from_ms_path(path: Path) -> "ReactionKey":
        """Create from a mass spectrum path.

        Parameters:
            path:
                The path to the mass spectrum directory.

        Returns:
            A reaction key.
        """
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_title_file(title_file: Path) -> "ReactionKey":
        """Create from a title file.

        The title file should contain the experiment, plate, and formulation
        number in the following format
        ``experiment_plate_formulation_number``.

        Parameters:
            title_file:
                The path to the title file.

        Returns:
            A reaction key.
        """
        title = title_file.read_text()
        experiment, plate, formulation_number = title.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_json_file(json_file: Path) -> "ReactionKey":
        """Create from a JSON file.

        The JSON file should contain the ``"experiment"``,
        ``"plate"``, and ``"formulation_number"`` keys.

        Parameters:
            json_file:
                The path to the JSON file.

        Returns:
            A reaction key.
        """
        with json_file.open() as file:
            data = json.load(file)
        return ReactionKey(
            experiment=data["experiment"],
            plate=data["plate"],
            formulation_number=data["formulation_number"],
        )


@dataclass(frozen=True, slots=True)
class Precursor:
    """A reaction precursor.

    Parameters:
        name: The name of the precursor.
        smiles: The SMILES string of the precursor.
    """

    name: str
    """The name of the precursor."""
    smiles: str
    """The SMILES string of the precursor."""


@dataclass(frozen=True, slots=True)
class Reaction:
    """A reaction.

    Parameters:
        experiment: The name of the experiment.
        plate: The plate number.
        formulation_number: The formulation number.
        di_name: The di-topic precursor.
        tri_name: The tri-topic precursor.
    """

    experiment: str
    """The name of the experiment."""
    plate: int
    """The plate number."""
    formulation_number: int
    """The formulation number."""
    di_name: str
    """The di-topic precursor."""
    tri_name: str
    """The tri-topic precursor."""


@dataclass(frozen=True, slots=True)
class MassSpectrumPeak:
    """A peak in a mass spectrum.

    Parameters:
        di_count: The number of di-topic precursors.
        tri_count: The number of tri-topic precursors.
        adduct: The adduct.
        charge: The charge.
        calculated_mz: The calculated m/z.
        spectrum_mz: The m/z from the spectrum.
        separation_mz: The separation peak m/z.
        intensity: The intensity of the peak.
    """

    di_count: int
    """The number of di-topic precusors."""
    tri_count: int
    """The number of tri-topic precursors."""
    adduct: str
    """The adduct."""
    charge: int
    """The charge."""
    calculated_mz: float
    """The calculated m/z."""
    spectrum_mz: float
    """The m/z from the spectrum."""
    separation_mz: float
    """The separation peak m/z."""
    intensity: float
    """The intensity of the peak."""


@dataclass(frozen=True, slots=True)
class MassSpectrumTopologyAssignment:
    """A topology assignment for a mass spectrum peak.

    Parameters:
        mass_spectrum_peak_id: The mass spectrum peak id.
        topology: The topology.
    """

    mass_spectrum_peak_id: int
    """The mass spectrum peak id."""
    topology: str
    """The topology."""


@dataclass(frozen=True, slots=True)
class Precursors:
    """The precursors for a reaction.

    Parameters:
        di_smiles: The SMILES string of the di-topic precursor.
        tri_smiles: The SMILES string of the tri-topic precursor.
    """

    di_smiles: str
    """The SMILES string of the di-topic precursor."""
    tri_smiles: str
    """The SMILES string of the tri-topic precursor."""


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Row(Generic[T]):
    """A row in a database table.

    Parameters:
        id: The id of the row.
        item: The item in the row.
    """

    id: int
    """The id of the row."""
    item: T
    """The item in the row."""


MassSpectrumId = NewType("MassSpectrumId", int)
MassSpectrumPeakId = NewType("MassSpectrumPeakId", int)


@dataclass(frozen=True, slots=True)
class NmrPeak:
    """An NMR peak.

    Parameters:
        ppm: The ppm.
        amplitude: The amplitude.
    """

    ppm: float
    """The ppm."""
    amplitude: float
    """The amplitude."""

    def in_range(self, min_ppm: float, max_ppm: float) -> bool:
        """Check if the peak is in the ppm given range.

        Parameters:
            min_ppm: The minimum ppm.
            max_ppm: The maximum ppm.

        Returns:
            ``True`` if the peak is in the ppm range, ``False`` otherwise.
        """
        return min_ppm < self.ppm < max_ppm

    def has_ppm(self, ppm: float, atol: float = 0.05) -> bool:
        """Check if the peak has the given ppm.

        Parameters:
            ppm: The ppm.
            atol: The absolute tolerance.

        Returns:
            ``True`` if the peak has the ppm, ``False`` otherwise.
        """
        return self.in_range(ppm - atol, ppm + atol)


NmrSpectrumId = NewType("NmrSpectrumId", int)
NmrAldehydePeakId = NewType("NmrAldehydePeakId", int)
NmrIminePeakId = NewType("NmrIminePeakId", int)


@dataclass(frozen=True, slots=True)
class NmrSpectrum:
    """An NMR spectrum.

    Parameters:
        aldehyde_peaks: The aldehyde peaks.
        imine_peaks: The imine peaks.
    """

    aldehyde_peaks: Sequence[NmrPeak]
    """The aldehyde peaks."""
    imine_peaks: Sequence[NmrPeak]
    """The imine peaks."""


class TurbidState(Enum):
    """The turbidity of a reaction solution."""

    DISSOLVED = "dissolved"
    """The solution is dissolved."""
    TURBID = "turbid"
    """The solution is turbid."""
    UNSTABLE = "unstable"
    """The solution state could not be determined."""
