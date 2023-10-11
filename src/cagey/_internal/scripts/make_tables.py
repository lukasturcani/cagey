import argparse
from pathlib import Path

from cagey import make_tables


def main() -> None:
    args = _parse_args()
    make_tables(args.database)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    return parser.parse_args()
