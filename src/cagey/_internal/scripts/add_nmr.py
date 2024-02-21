from collections.abc import Iterable
from pathlib import Path
from sqlite3 import Connection

from rich.progress import Progress, TaskID

import cagey
from cagey import ReactionKey


def main(
    connection: Connection,
    title_files: Iterable[Path],
    progress: Progress,
    task_id: TaskID,
) -> None:
    progress.start_task(task_id)
    for path in progress.track(title_files, task_id=task_id):
        cagey.queries.insert_nmr_spectrum(
            connection,
            ReactionKey.from_title_file(path),
            cagey.nmr.get_spectrum(path.parent),
            commit=False,
        )
    connection.commit()
