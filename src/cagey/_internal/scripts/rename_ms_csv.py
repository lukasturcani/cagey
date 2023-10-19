import argparse
from pathlib import Path
from typing import cast


def main() -> None:
    args = _parse_args()
    for csv in cast(list[Path], args.csv):
        experiment, plate_data, _ = csv.stem.split("_")
        plate, formulation_number = plate_data.split("-")
        plate = plate.removeprefix("P")
        stem = "_".join([experiment, plate, formulation_number])
        csv.rename(csv.parent / f"{stem}.csv")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    main()
