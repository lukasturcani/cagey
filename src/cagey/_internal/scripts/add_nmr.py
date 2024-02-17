from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.progress import Progress, TaskID
from sqlmodel import Session, and_, or_, select

import cagey
from cagey.tables import Reaction


def main(
    session: Session,
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


@dataclass(frozen=True, slots=True)
class ReactionKey:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_title_file(title_file: Path) -> "ReactionKey":
        title = title_file.read_text()
        experiment, plate, formulation_number = title.split("_")
        return ReactionKey(experiment, int(plate), int(formulation_number))

    @staticmethod
    def from_reaction(reaction: Reaction) -> "ReactionKey":
        return ReactionKey(
            reaction.experiment, reaction.plate, reaction.formulation_number
        )


def _get_reaction_query(reaction_key: ReactionKey) -> Any:
    return and_(
        Reaction.experiment == reaction_key.experiment,
        Reaction.plate == reaction_key.plate,
        Reaction.formulation_number == reaction_key.formulation_number,
    )
