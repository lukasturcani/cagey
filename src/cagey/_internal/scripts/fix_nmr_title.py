# ruff: noqa: T201

import argparse
from pathlib import Path
from typing import cast


def main() -> None:
    args = _parse_args()
    for title_file in cast(list[Path], args.title_file):
        title = title_file.read_text()
        try:
            experiment, plate_data = title.strip().split()
            plate, formulation_number = plate_data.split("-")
        except ValueError:
            *experiment_, plate, formulation_number = title.strip().split("-")
            if len(experiment_) == 2 and plate == "P2":  # noqa: PLR2004
                experiment = "AB-02-009"
            elif len(experiment_) != 3:  # noqa: PLR2004
                print(f"bad file: {title_file}")
                continue
            else:
                experiment = "-".join(experiment_)

        new_title = "_".join(
            [
                experiment.replace("AB-01-005", "AB-02-005"),
                plate.removeprefix("P").replace("2B", "4").zfill(2),
                formulation_number.zfill(2),
            ]
        )
        title_file.write_text(f"{new_title}\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("title_file", type=Path, nargs="+")
    return parser.parse_args()


if __name__ == "__main__":
    main()
