# ruff: noqa: T201

import pkgutil
import subprocess
import tempfile
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from multiprocessing import Pool
from pathlib import Path
from typing import Any, assert_never

from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from sqlalchemy.orm import aliased
from sqlmodel import Session, and_, or_, select

import cagey
from cagey.tables import MassSpectrum, Precursor, Reaction

Di = aliased(Precursor)
Tri = aliased(Precursor)


def main(
    session: Session,
    machine_data: Sequence[Path],
    mzmine: Path,
) -> None:
    reaction_keys = tuple(map(ReactionKey.from_path, machine_data))
    reaction_query = select(Reaction, Di, Tri).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )

    reactions = {
        ReactionKey.from_reaction(reaction): ReactionData(
            reaction=reaction, di=di, tri=tri
        )
        for reaction, di, tri in session.exec(reaction_query).all()
    }
    get_mass_spectrum = partial(_get_mass_spectrum, mzmine)
    with Pool() as pool:
        failures = []
        spectrums = []
        with Progress(
            SpinnerColumn(
                spinner_name="bouncingBall",
                finished_text="[green]:heavy_check_mark:",
            ),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            transient=False,
        ) as progress:
            for result in progress.track(
                pool.imap_unordered(
                    get_mass_spectrum,
                    map(
                        partial(_get_mass_spectrum_input, reactions),
                        machine_data,
                    ),
                ),
                description="Adding mass spectra",
                total=len(machine_data),
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
        print(f"failed to process: [\n{failures_repr},\n]")
    session.add_all(spectrums)
    session.commit()
    with Progress(
        SpinnerColumn(
            spinner_name="bouncingBall",
            finished_text="[green]:heavy_check_mark:",
        ),
        *Progress.get_default_columns(),
        TimeElapsedColumn(),
        transient=False,
    ) as progress:
        for spectrum in progress.track(
            spectrums, description="Adding topology assignments"
        ):
            session.add_all(cagey.ms.get_topologies(spectrum))
    session.commit()


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionKey":
        experiment, plate, formulation_number = path.stem.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_reaction(reaction: Reaction) -> "ReactionKey":
        return ReactionKey(
            reaction.experiment, reaction.plate, reaction.formulation_number
        )


@dataclass(frozen=True, slots=True)
class ReactionData:
    reaction: Reaction
    di: Precursor
    tri: Precursor


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
            csv, reaction_data.reaction, reaction_data.di, reaction_data.tri
        )
    # catch any exception here because the function get called in a
    # process pool
    except Exception as ex:  # noqa: BLE001
        return MassSpectrumError(machine_data, ex)
