# ruff: noqa: T201

import argparse
from pathlib import Path
from typing import cast


def main() -> None:
    args = _parse_args()
    for csv in cast(list[Path], args.csv):
        try:
            experiment, plate_data, _ = csv.stem.split("_")
            plate, formulation_number = plate_data.split("-")
        except ValueError:
            data, _ = csv.stem.split("_")
            *experiment_, plate, formulation_number = data.split("-")
            if len(experiment_) != 3:  # noqa: PLR2004
                print(f"bad file: {csv}")
                continue
            experiment = "-".join(experiment_)

        stem = "_".join(
            [
                experiment,
                plate.removeprefix("P").replace("2B", "4").zfill(2),
                formulation_number.zfill(2),
            ]
        )
        csv.rename(csv.parent / f"{stem}.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    main()
