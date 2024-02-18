from collections.abc import Sequence
from pathlib import Path
from sqlite3 import Connection

from rich.progress import Progress, TaskID

import cagey


def main(
    session: Connection,
    title_files: Sequence[Path],
    progress: Progress,
    task_id: TaskID,
) -> None:
    reaction_keys = tuple(map(ReactionKey.from_title_file, title_files))
    reaction_query = select(Reaction).where(
        or_(*map(_get_reaction_query, reaction_keys))
    )
    reactions = {
        ReactionKey.from_reaction(reaction): reaction
        for reaction in session.exec(reaction_query).all()
    }
    progress.start_task(task_id)
    for path, reaction_key in progress.track(
        zip(title_files, reaction_keys, strict=True),
        task_id=task_id,
    ):
        reaction = reactions[reaction_key]
        session.add(cagey.nmr.get_spectrum(path.parent, reaction))
    session.commit()
