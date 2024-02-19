import pkgutil
import subprocess
import tempfile
import textwrap
from collections.abc import Sequence
from dataclasses import dataclass
from functools import partial
from multiprocessing.pool import Pool
from pathlib import Path
from sqlite3 import Connection
from typing import assert_never

from rich import print
from rich.progress import Progress, TaskID

import cagey
from cagey.queries import Precursors, ReactionKey, Row


def main(  # noqa: PLR0913
    connection: Connection,
    machine_data: Sequence[Path],
    mzmine: Path,
    progress: Progress,
    task_id: TaskID,
    pool: Pool,
) -> None:
    reaction_keys = tuple(map(ReactionKey.from_ms_path, machine_data))
    paths = dict(zip(reaction_keys, machine_data, strict=True))
    precursors = cagey.queries.reaction_precursors(connection, reaction_keys)

    failures = []
    spectrums = []
    progress.start_task(task_id)
    for result in progress.track(
        pool.imap_unordered(
            partial(_get_mass_spectrum, mzmine),
            (
                (reaction_key, precursors, paths[reaction_key])
                for reaction_key, precursors in precursors
            ),
        ),
        task_id=task_id,
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
    for spectrum in spectrums:
        _, max_peak_id = cagey.queries.insert_mass_spectrum(
            connection, spectrum.reaction_key, spectrum.peaks, commit=False
        )
        cagey.queries.insert_mass_spectrum_topology_assignments(
            connection,
            cagey.ms.get_topologies(
                Row(peak_id, peak)
                for peak_id, peak in enumerate(
                    spectrum.peaks,
                    max_peak_id + 1 - len(spectrum.peaks),
                )
            ),
            commit=False,
        )
    connection.commit()


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


@dataclass(frozen=True, slots=True)
class MassSpectrum:
    reaction_key: ReactionKey
    peaks: list[cagey.ms.MassSpectrumPeak]


def _get_mass_spectrum(
    mzmine: Path,
    spectrum_data: tuple[ReactionKey, Precursors, Path],
) -> MassSpectrum | MassSpectrumError:
    try:
        reaction_key, precursors, machine_data = spectrum_data
        mzml = _to_mzml(machine_data)
        csv = _mzml_to_csv(mzml, mzmine)
        return MassSpectrum(
            reaction_key,
            list(
                cagey.ms.get_peaks(
                    csv,
                    precursors.di_smiles,
                    precursors.tri_smiles,
                )
            ),
        )
    # catch any exception here because the function get called in a
    # process pool
    except Exception as ex:  # noqa: BLE001
        return MassSpectrumError(machine_data, ex)
