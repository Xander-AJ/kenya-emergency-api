"""CLI: python scripts/build_db.py [--snapshots PATH] [--out PATH]

Builds the SQLite database from JSON snapshots and prints the resulting
StorageMetadata as pretty JSON. Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from kenya_emergency.core.config import DEFAULT_SNAPSHOT_DIR, Settings
from kenya_emergency.core.exceptions import KenyaEmergencyError
from kenya_emergency.storage import build_database


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help="Directory of JSON snapshots (default: bundled snapshots).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Settings().db_path,
        help="Output path for the built SQLite database (default: configured db_path).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build the database and print its metadata. Returns a process exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parse_args(argv)
    try:
        metadata = build_database(args.snapshots, args.out)
    except KenyaEmergencyError as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    print(metadata.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
