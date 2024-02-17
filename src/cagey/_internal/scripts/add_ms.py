import pkgutil
import subprocess
import tempfile
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from sqlite3 import Connection
from typing import Any, assert_never

from rich import print
from rich.progress import Progress, TaskID

import cagey
from cagey.tables import MassSpectrum, Precursor, Reaction


def main(  # noqa: PLR0913
    connection: Connection,
    machine_data: Sequence[Path],
    mzmine: Path,
    progress: Progress,
    ms_task: TaskID,
    topology_assignment_task: TaskID,
) -> None:
    reaction_keys = tuple(map(ReactionKey.from_path, machine_data))
    reaction_query = select(Reaction, Di, Tri).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )

    reactions = {
        ReactionKey.from_reaction(reaction): ReactionData(
            reaction=_Reaction.from_reaction(reaction),
            di=_Precursor.from_precursor(di),
            tri=_Precursor.from_precursor(tri),
        )
        for reaction, di, tri in session.exec(reaction_query).all()
    }
    get_mass_spectrum = partial(_get_mass_spectrum, mzmine)
    with Pool() as pool:
        failures = []
        spectrums = []
        progress.start_task(ms_task)
        for result in progress.track(
            pool.imap_unordered(
                get_mass_spectrum,
                map(
                    partial(_get_mass_spectrum_input, reactions),
                    machine_data,
                ),
            ),
            task_id=ms_task,
        ):
            match result:
                case MassSpectrum():
                    spectrums.append(result)
                case MassSpectrumError():
                    failures.append(result)
                case _ as unreachable:
                    assert_never(unreachable)
    if failures:
        failures_repr = textwrap.indent(
            text="\n".join(failure.to_str() for failure in failures),
            prefix="\t",
        )
        print(f"failed to process ms spectra: [\n{failures_repr}\n]")
    session.add_all(spectrums)
    session.commit()
    progress.start_task(topology_assignment_task)
    for spectrum in progress.track(
        spectrums,
        description="Adding topology assignments",
        task_id=topology_assignment_task,
    ):
        session.add_all(cagey.ms.get_topologies(spectrum))
    session.commit()


@dataclass(frozen=True, slots=True)
class _Reaction:
    id: int
    experiment: str
    plate: int
    formulation_number: int
    di_name: str
    tri_name: str

    @staticmethod
    def from_reaction(reaction: Reaction) -> "_Reaction":
        if not isinstance(reaction.id, int):
            msg = f"reaction id is not an int: {reaction}"
            raise TypeError(msg)
        return _Reaction(
            id=reaction.id,
            experiment=reaction.experiment,
            plate=reaction.plate,
            formulation_number=reaction.formulation_number,
            di_name=reaction.di_name,
            tri_name=reaction.tri_name,
        )

    def to_reaction(self) -> Reaction:
        return Reaction(
            id=self.id,
            experiment=self.experiment,
            plate=self.plate,
            formulation_number=self.formulation_number,
            di_name=self.di_name,
            tri_name=self.tri_name,
        )


@dataclass(frozen=True, slots=True)
class _Precursor:
    name: str
    smiles: str

    @staticmethod
    def from_precursor(precursor: Precursor) -> "_Precursor":
        return _Precursor(name=precursor.name, smiles=precursor.smiles)

    def to_precursor(self) -> Precursor:
        return Precursor(name=self.name, smiles=self.smiles)


@dataclass(frozen=True, slots=True)
class ReactionData:
    reaction: _Reaction
    di: _Precursor
    tri: _Precursor


def _get_mass_spectrum_input(
    reactions: dict[ReactionKey, ReactionData],
    machine_data: Path,
) -> tuple[ReactionData, Path]:
    reaction_key = ReactionKey.from_path(machine_data)
    return reactions[reaction_key], machine_data


def _get_reaction_query(reaction_key: ReactionKey) -> Any:
    return and_(
        Reaction.experiment == reaction_key.experiment,
        Reaction.plate == reaction_key.plate,
        Reaction.formulation_number == reaction_key.formulation_number,
        Di.name == Reaction.di_name,
        Tri.name == Reaction.tri_name,
    )


def _to_mzml(
    machine_data: Path,
) -> Path:
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


def _mzml_to_csv(mzml: Path, mzmine: Path) -> Path:
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


@dataclass(frozen=True, slots=True)
class MassSpectrumError:
    path: Path
    exception: Exception

    def to_str(self) -> str:
        error_str = textwrap.indent(
            text=str(self.exception),
            prefix="\t",
        )
        return f"{self.path}:\n{error_str}"


def _get_mass_spectrum(
    mzmine: Path,
    spectrum_data: tuple[ReactionData, Path],
) -> MassSpectrum | MassSpectrumError:
    try:
        reaction_data, machine_data = spectrum_data
        mzml = _to_mzml(machine_data)
        csv = _mzml_to_csv(mzml, mzmine)
        return cagey.ms.get_spectrum(
            csv,
            reaction_data.reaction.to_reaction(),
            reaction_data.di.to_precursor(),
            reaction_data.tri.to_precursor(),
        )
    # catch any exception here because the function get called in a
    # process pool
    except Exception as ex:  # noqa: BLE001
        return MassSpectrumError(machine_data, ex)
