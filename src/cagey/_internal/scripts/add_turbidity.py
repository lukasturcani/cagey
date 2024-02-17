import json
from collections.abc import Sequence
from pathlib import Path
from typing import TypedDict

from rich.progress import Progress, TaskID
from sqlmodel import Session, select

import cagey
from cagey.tables import (
    Reaction,
    Turbidity,
    TurbidityDissolvedReference,
    TurbidityMeasurement,
)


def main(
    session: Session,
    data_files: Sequence[Path],
    progress: Progress,
    task_id: TaskID,
) -> None:
    progress.start_task(task_id)
    for path in progress.track(data_files, task_id=task_id):
        data = _read_json(path)
        dissolved_reference = data["turbidity_dissolved_reference"]
        reaction_query = select(Reaction).where(
            Reaction.experiment == data["experiment"],
            Reaction.plate == data["plate"],
            Reaction.formulation_number == data["formulation_number"],
        )
        reaction = session.exec(reaction_query).one()
        session.add(
            Turbidity(
                reaction_id=reaction.id,
                state=cagey.turbidity.get_turbid_state(
                    data["turbidity_data"], dissolved_reference
                ),
            )
        )
        session.add(
            TurbidityDissolvedReference(
                reaction_id=reaction.id,
                dissolved_reference=dissolved_reference,
            )
        )
        session.add_all(
            TurbidityMeasurement(
                reaction_id=reaction.id, time=time, turbidity=turbidity
            )
            for time, turbidity in data["turbidity_data"].items()
        )
    session.commit()


class TurbidityData(TypedDict):
    experiment: str
    plate: int
    formulation_number: int
    turbidity_data: dict[str, float]
    turbidity_dissolved_reference: float


def _read_json(path: Path) -> TurbidityData:
    with path.open() as file:
        return json.load(file)
