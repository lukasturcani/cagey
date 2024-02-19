from collections.abc import Sequence
from pathlib import Path
from sqlite3 import Connection

from rich.progress import Progress, TaskID

import cagey
from cagey.queries import ReactionKey


def main(
    connection: Connection,
    title_files: Sequence[Path],
    progress: Progress,
    task_id: TaskID,
) -> None:
    reaction_keys = tuple(map(ReactionKey.from_title_file, title_files))
    progress.start_task(task_id)
    for path, reaction_key in progress.track(
        zip(title_files, reaction_keys, strict=True),
        task_id=task_id,
    ):
        cagey.queries.insert_nmr_spectrum(
            connection,
            reactions[reaction_key],
            cagey.nmr.get_spectrum(path.parent),
            commit=False,
        )
    connection.commit()
