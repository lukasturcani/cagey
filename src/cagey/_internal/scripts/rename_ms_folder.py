import argparse
from pathlib import Path
from typing import cast


def main() -> None:
    args = _parse_args()
    for folder in cast(list[Path], args.folder):
        try:
            experiment, plate_data = folder.stem.split("_")
            plate, formulation_number = plate_data.split("-")
        except ValueError:
            *experiment_, plate, formulation_number = folder.stem.split("-")
            if len(experiment_) != 3:
                print(f"bad folder: {folder}")
                continue
            experiment = "-".join(experiment_)

        stem = "_".join(
            [
                experiment,
                plate.removeprefix("P").replace("2B", "4").zfill(2),
                formulation_number.zfill(2),
            ]
        )
        folder.rename(folder.parent / f"{stem}.d")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    main()
