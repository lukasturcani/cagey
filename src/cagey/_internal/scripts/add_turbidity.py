import argparse
import json
from enum import Enum, auto
from pathlib import Path
from typing import TypeAlias

Json: TypeAlias = int | float | str | None | list["Json"] | dict[str, "Json"]


class TurbidState(Enum):
    DISSOLVED = auto()
    SATURATED = auto()
    STABLE = auto()
    UNSTABLE = auto()


def main() -> None:
    args = _parse_args()
    for path in args.data:
        data = _read_json(path)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("data", type=Path, nargs="+")
    return parser.parse_args()


def _read_json(path: Path) -> Json:
    with path.open() as file:
        return json.load(file)
