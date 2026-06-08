"""Canonical build pipeline: JSON snapshots -> validated SQLite database.

The build is all-or-nothing. Every record is validated through its Pydantic
model (including phone-number E.164 normalization) before any database file is
touched, and the finished database is moved into place with an atomic
``os.replace`` so a failed build can never leave a partial or corrupt DB.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from collections.abc import Callable, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, NamedTuple, cast

from pydantic import BaseModel, ValidationError

from kenya_emergency.core.exceptions import StorageError
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.storage import _serde
from kenya_emergency.storage.base import StorageMetadata
from kenya_emergency.storage.schema import SCHEMA_SQL

logger = logging.getLogger(__name__)


class _TableSpec(NamedTuple):
    """Binds a snapshot file to its model, table, and conversion functions."""

    filename: str
    table: str
    model: type[BaseModel]
    insert_sql: str
    to_params: Callable[[Any], dict[str, Any]]


_TABLE_SPECS: tuple[_TableSpec, ...] = (
    _TableSpec(
        "counties_v1.json", "counties", County, _serde.INSERT_COUNTY, _serde.county_params
    ),
    _TableSpec(
        "emergency_contacts_v1.json",
        "emergency_contacts",
        EmergencyContact,
        _serde.INSERT_EMERGENCY_CONTACT,
        _serde.emergency_contact_params,
    ),
    _TableSpec(
        "national_emergency_numbers_v1.json",
        "national_numbers",
        NationalNumber,
        _serde.INSERT_NATIONAL_NUMBER,
        _serde.national_number_params,
    ),
    _TableSpec(
        "poison_control_v1.json",
        "poison_controls",
        PoisonControl,
        _serde.INSERT_POISON_CONTROL,
        _serde.poison_control_params,
    ),
)


def _load_snapshot(snapshot_dir: Path, spec: _TableSpec) -> list[Any]:
    """Read, parse, and validate one snapshot file into model instances.

    Raises:
        StorageError: If the file is missing, not valid JSON, not a JSON array,
            or contains a record that fails model validation. The message names
            the file and, for validation failures, the offending index.
    """
    path = snapshot_dir / spec.filename
    if not path.exists():
        raise StorageError(f"Snapshot file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StorageError(f"Snapshot file {path} is not valid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise StorageError(f"Snapshot file {path} must contain a JSON array")

    if not data:
        logger.warning("Snapshot %s is empty; writing zero rows", path)
        return []

    records: list[Any] = []
    for index, item in enumerate(data):
        try:
            records.append(spec.model.model_validate(item))
        except ValidationError as exc:
            raise StorageError(
                f"Invalid record in {path} at index {index}: {exc}"
            ) from exc
    return records


def _max_verified_at(records: Sequence[Any]) -> date | None:
    """Return the latest provenance.last_verified_at across records, or None."""
    if not records:
        return None
    return cast(date, max(record.provenance.last_verified_at for record in records))


def _write_database(
    tmp_path: Path,
    loaded: dict[str, list[Any]],
    metadata: StorageMetadata,
) -> None:
    """Create the schema, insert all records, and persist metadata to ``tmp_path``."""
    conn = sqlite3.connect(tmp_path)
    try:
        conn.executescript(SCHEMA_SQL)
        for spec in _TABLE_SPECS:
            records = loaded[spec.filename]
            if records:
                conn.executemany(
                    spec.insert_sql, [spec.to_params(record) for record in records]
                )
        conn.executemany(
            "INSERT INTO _metadata (key, value) VALUES (:key, :value)",
            [
                {"key": "built_at", "value": json.dumps(metadata.built_at.isoformat())},
                {
                    "key": "snapshot_versions",
                    "value": json.dumps(
                        {fn: d.isoformat() for fn, d in metadata.snapshot_versions.items()}
                    ),
                },
                {"key": "record_counts", "value": json.dumps(metadata.record_counts)},
            ],
        )
        conn.commit()
    finally:
        conn.close()


def build_database(snapshot_dir: Path, db_path: Path) -> StorageMetadata:
    """Build the SQLite database from JSON snapshots.

    Reads four files from ``snapshot_dir``:

    - ``counties_v1.json`` -> ``list[County]``
    - ``emergency_contacts_v1.json`` -> ``list[EmergencyContact]``
    - ``national_emergency_numbers_v1.json`` -> ``list[NationalNumber]``
    - ``poison_control_v1.json`` -> ``list[PoisonControl]``

    Each file is parsed as a JSON array and every item is validated through its
    Pydantic model (full validation, including phone E.164 normalization).
    Invalid records raise :class:`StorageError` naming the file, index, and the
    pydantic error chain.

    The database is built into ``{db_path}.tmp``, fsynced, then atomically renamed
    onto ``db_path`` via :func:`os.replace`, so a failed build never leaves a
    partial database and never disturbs an existing one.

    Args:
        snapshot_dir: Directory containing the four snapshot files.
        db_path: Destination path for the built database.

    Returns:
        :class:`StorageMetadata` describing what was built.

    Raises:
        StorageError: If a snapshot file is missing, malformed, or contains an
            invalid record. An empty snapshot file is allowed (a warning is
            logged and zero rows are written).
    """
    start = time.perf_counter()
    logger.info("Building DB from %s → %s", snapshot_dir, db_path)

    # Validate everything up front: nothing is written unless all snapshots load.
    loaded: dict[str, list[Any]] = {}
    record_counts: dict[str, int] = {}
    snapshot_versions: dict[str, date] = {}
    for spec in _TABLE_SPECS:
        records = _load_snapshot(snapshot_dir, spec)
        loaded[spec.filename] = records
        record_counts[spec.table] = len(records)
        latest = _max_verified_at(records)
        if latest is not None:
            snapshot_versions[spec.filename] = latest

    metadata = StorageMetadata(
        built_at=datetime.now(UTC),
        snapshot_versions=snapshot_versions,
        record_counts=record_counts,
    )

    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = Path(f"{db_path}.tmp")
    try:
        _write_database(tmp_path, loaded, metadata)
        # Durably flush the finished file before swapping it into place.
        fd = os.open(tmp_path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp_path, db_path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise

    duration = time.perf_counter() - start
    for table, count in record_counts.items():
        logger.info("  %s: %d rows", table, count)
    logger.info("Built %s in %.3fs", db_path, duration)
    return metadata
