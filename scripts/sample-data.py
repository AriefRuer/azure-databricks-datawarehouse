#!/usr/bin/env python3
"""sample-data.py — generate 1,000-row sample CSVs for the git repo.

Reads the full RetailRocket CSVs from the local (gitignored) raw folder and
writes the first 1,000 rows of each logical file into 02-data/samples/ so
notebooks and CI can run WITHOUT any Azure access.

This script never talks to Azure — it only reads local files.
Handles Kaggle's split files: item_properties_part1.csv + part2.csv are
streamed in order and treated as one logical item_properties.csv sample.

Usage:
    python scripts/sample-data.py                          # defaults: data-retailrocket -> 02-data/samples
    python scripts/sample-data.py --input /path/to/kaggle  # point at your Kaggle download folder
"""

import argparse
import csv
from pathlib import Path

SAMPLE_ROWS = 1_000

# logical sample name -> glob pattern(s) in the input folder
FILE_PATTERNS = {
    "events.csv": ["events.csv"],
    "category_tree.csv": ["category_tree.csv"],
    "item_properties.csv": ["item_properties*.csv"],
}


def sample_file(src_files: list[Path], dst: Path, n: int) -> int:
    """Copy the header + first n rows across src_files (in order) into dst.

    Returns rows copied. Reads only n rows total — fast even on the
    900 MB split item_properties files.
    """
    with dst.open("w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        header_written = False
        rows = 0
        for src in src_files:
            with src.open(newline="", encoding="utf-8") as f_in:
                reader = csv.reader(f_in)
                header = next(reader)
                if not header_written:
                    writer.writerow(header)
                    header_written = True
                for row in reader:
                    if rows >= n:
                        return rows
                    writer.writerow(row)
                    rows += 1
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 1,000-row sample CSVs from the full RetailRocket files."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data-retailrocket"),
        help="Folder with the full CSVs (default: data-retailrocket, gitignored)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("02-data/samples"),
        help="Folder for sample CSVs (default: 02-data/samples, committed)",
    )
    parser.add_argument(
        "--rows", type=int, default=SAMPLE_ROWS, help=f"Rows per sample (default: {SAMPLE_ROWS})"
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    missing = [
        f"{name} ({', '.join(patterns)})"
        for name, patterns in FILE_PATTERNS.items()
        if not any((args.input / p).exists() or list(args.input.glob(p)) for p in patterns)
    ]
    if missing:
        parser.error(
            f"Missing input files in {args.input}: {', '.join(missing)}\n"
            "Put the Kaggle CSVs here first — this folder is gitignored, "
            "so the full files never get committed."
        )

    for name, patterns in FILE_PATTERNS.items():
        src_files = sorted(args.input.glob(p) for p in patterns)
        src_files = sorted({f for group in src_files for f in group})
        dst = args.output / name
        rows = sample_file(src_files, dst, args.rows)
        sources = ", ".join(f.name for f in src_files)
        print(f"{name}: {rows} rows <- {sources} -> {dst}")

    print(
        f"\nDone. Commit 02-data/samples/ (the full files in {args.input}/ stay gitignored).\n"
        "Notebooks and CI can now run against the samples with no Azure access."
    )


if __name__ == "__main__":
    main()
