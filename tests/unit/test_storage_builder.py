"""Unit tests for the database build pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from kenya_emergency.core.exceptions import StorageError
from kenya_emergency.storage import build_database


def _copy_snapshots(snapshot_dir: Path, dest: Path) -> Path:
    """Copy the fixture snapshots into a writable temp directory."""
    dest.mkdir(parents=True, exist_ok=True)
    for path in snapshot_dir.glob("*.json"):
        shutil.copy(path, dest / path.name)
    return dest


def test_build_succeeds_returns_metadata(tmp_path: Path, snapshot_dir: Path) -> None:
    """A valid build writes the DB and returns accurate record counts."""
    db_path = tmp_path / "out.db"

    metadata = build_database(snapshot_dir, db_path)

    assert db_path.exists()
    assert metadata.record_counts == {
        "counties": 2,
        "emergency_contacts": 4,
        "national_numbers": 2,
        "poison_controls": 1,
    }
    # snapshot_versions carries the max last_verified_at per file.
    assert metadata.snapshot_versions["counties_v1.json"].isoformat() == "2026-01-15"


def test_missing_snapshot_file_raises(tmp_path: Path) -> None:
    """A missing snapshot file raises StorageError naming the path."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(StorageError) as exc_info:
        build_database(empty_dir, tmp_path / "out.db")

    assert "counties_v1.json" in str(exc_info.value)


def test_invalid_record_raises_with_file_and_index(
    tmp_path: Path, snapshot_dir: Path
) -> None:
    """An invalid record raises StorageError naming the file and offending index."""
    snaps = _copy_snapshots(snapshot_dir, tmp_path / "snaps")
    (snaps / "emergency_contacts_v1.json").write_text(
        """
        [
          {
            "county_code": "047",
            "category": "police",
            "name": "Bad Phone Station",
            "phone_numbers": ["not-a-phone"],
            "notes": null,
            "provenance": {
              "source": "Test",
              "source_url": null,
              "last_verified_at": "2026-01-12",
              "verification_method": "manual_call",
              "notes": null
            }
          }
        ]
        """,
        encoding="utf-8",
    )

    with pytest.raises(StorageError) as exc_info:
        build_database(snaps, tmp_path / "out.db")

    message = str(exc_info.value)
    assert "emergency_contacts_v1.json" in message
    assert "index 0" in message


def test_failed_build_is_atomic(tmp_path: Path, snapshot_dir: Path) -> None:
    """A corrupt snapshot fails cleanly: tmp removed, existing DB untouched."""
    snaps = _copy_snapshots(snapshot_dir, tmp_path / "snaps")
    (snaps / "poison_control_v1.json").write_text("{ this is not json", encoding="utf-8")

    db_path = tmp_path / "out.db"
    db_path.write_bytes(b"SENTINEL")  # pre-existing DB must survive a failed build

    with pytest.raises(StorageError):
        build_database(snaps, db_path)

    assert db_path.read_bytes() == b"SENTINEL"
    assert not Path(f"{db_path}.tmp").exists()
