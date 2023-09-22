import argparse
from pathlib import Path


def main() -> None:
    args = _parse_args()

    for spectrum in args.nmr_directory.glob("**/pdata/1/1r"):
        spectrum_dir = spectrum.parent
        title = spectrum_dir.joinpath("title").read_text()
        experiment = title[:9]
        try:
            plate, _ = title[10:].split("-")
        except ValueError:
            print(title)
            continue
        formulation_number = int(title[title.rfind("-") + 1 :])
        spectrum_dir.joinpath("title").write_text(
            f"{experiment},{plate},{formulation_number}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("nmr_directory", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    main()
