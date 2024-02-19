import json
from collections.abc import Sequence
from pathlib import Path
from sqlite3 import Connection
from typing import TypedDict

from rich.progress import Progress, TaskID

import cagey
from cagey.queries import ReactionKey


def main(
    connection: Connection,
    data_files: Sequence[Path],
    progress: Progress,
    task_id: TaskID,
) -> None:
    progress.start_task(task_id)
    for path in progress.track(data_files, task_id=task_id):
        data = _read_json(path)
        dissolved_reference = data["turbidity_dissolved_reference"]
        cagey.queries.insert_turbidity(
            connection,
            ReactionKey(
                experiment=data["experiment"],
                plate=data["plate"],
                formulation_number=data["formulation_number"],
            ),
            data.turbidity_dissolved_reference,
            data.turbidity_data,
        )
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
    connection.commit()


class TurbidityData(TypedDict):
    experiment: str
    plate: int
    formulation_number: int
    turbidity_data: dict[str, float]
    turbidity_dissolved_reference: float


def _read_json(path: Path) -> TurbidityData:
    with path.open() as file:
        return json.load(file)
