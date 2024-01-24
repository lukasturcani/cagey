import argparse
from pathlib import Path
from typing import cast


def main() -> None:
    args = _parse_args()
    for folder in cast(list[Path], args.folder):
        *head, formulation_number = folder.stem.split("_")
        new_stem = "_".join([*head, formulation_number.zfill(2)])
        folder.rename(folder.parent / new_stem)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, nargs="+")
    return parser.parse_args()
