import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ReactionData:
    experiment: str
    plate: int
    formulation_number: int

    @staticmethod
    def from_path(path: Path) -> "ReactionData":
        if "july23" in path.parent.name:
            path = path.parent
        return ReactionData(
            formulation_number=int(path.parent.name.split("_")[-1]),
            plate=int(path.parent.parent.name.lstrip("P")),
            experiment=path.parent.parent.parent.name,
        )


def main() -> None:
    args = _parse_args()
    for data_path in args.data:
        reaction_data = ReactionData.from_path(data_path)
        data = _read_json(data_path)
        data["experiment"] = reaction_data.experiment
        data["plate"] = reaction_data.plate
        data["formulation_number"] = reaction_data.formulation_number
        _write_json(data_path, data)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("data", type=Path, nargs="+")
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open() as file:
        return json.load(file)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w") as file:
        json.dump(data, file)
