"""SQLite storage adapter (default backend).

Reads from a SQLite database built from the vendored JSON snapshots. Rows are
always reconstructed through their Pydantic models, so reads double as schema
validation (and re-normalize phone numbers for free).

v1 keeps connection handling deliberately simple: one short-lived connection per
query. No pooling, no caching, no shared mutable connection — sqlite3 connections
are not thread-safe by default, and per-query connections sidestep that entirely.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Literal

from kenya_emergency.core.exceptions import DataNotFoundError, StorageError
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.storage import _serde
from kenya_emergency.storage.base import StorageAdapter, StorageMetadata
from kenya_emergency.storage.builder import build_database

logger = logging.getLogger(__name__)


class SQLiteAdapter(StorageAdapter):
    """Read-only adapter over a SQLite emergency-data database.

    On construction, if the database file is missing it is lazily built from
    ``snapshot_dir`` (when ``auto_build`` is enabled); otherwise a
    :class:`StorageError` explains how to build it.
    """

    def __init__(
        self,
        db_path: Path,
        snapshot_dir: Path | None = None,
        auto_build: bool = True,
    ) -> None:
        """Initialize the adapter, lazily building the database if needed.

        Args:
            db_path: Path to the SQLite database file.
            snapshot_dir: Directory of JSON snapshots used to build the database
                if it does not yet exist.
            auto_build: Whether to build the database from ``snapshot_dir`` when
                ``db_path`` is missing.

        Raises:
            StorageError: If the database is missing and cannot be auto-built
                (``auto_build`` disabled or no ``snapshot_dir`` given).
        """
        self._db_path = db_path
        if not db_path.exists():
            if auto_build and snapshot_dir is not None:
                logger.info("Database not found at %s, building from snapshots...", db_path)
                build_database(snapshot_dir, db_path)
            else:
                raise StorageError(
                    f"Database not found at {db_path}. Build it first by running "
                    f"scripts/build_db.py, or construct SQLiteAdapter with a "
                    f"snapshot_dir and auto_build=True."
                )

    def _connect(self) -> sqlite3.Connection:
        """Open a fresh connection configured for this adapter."""
        conn = sqlite3.connect(self._db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def get_county(self, code: str) -> County:
        """Return the county with the given code, or raise DataNotFoundError."""
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM counties WHERE code = ?", (code,)
            ).fetchone()
        if row is None:
            raise DataNotFoundError(f"No county with code {code!r}")
        return _serde.county_from_row(row)

    def list_counties(self) -> list[County]:
        """Return all counties, ordered by code."""
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM counties ORDER BY code").fetchall()
        return [_serde.county_from_row(row) for row in rows]

    def get_emergency_contacts(
        self, county_code: str, category: ContactCategory | None = None
    ) -> list[EmergencyContact]:
        """Return a county's emergency contacts, optionally filtered by category."""
        sql = "SELECT * FROM emergency_contacts WHERE county_code = ?"
        params: list[str] = [county_code]
        if category is not None:
            sql += " AND category = ?"
            params.append(category.value)
        sql += " ORDER BY id"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_serde.emergency_contact_from_row(row) for row in rows]

    def list_national_numbers(
        self, category: ContactCategory | None = None
    ) -> list[NationalNumber]:
        """Return national numbers, optionally filtered by category."""
        sql = "SELECT * FROM national_numbers"
        params: list[str] = []
        if category is not None:
            sql += " WHERE category = ?"
            params.append(category.value)
        sql += " ORDER BY id"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_serde.national_number_from_row(row) for row in rows]

    def list_poison_controls(
        self, scope: Literal["national", "regional"] | None = None
    ) -> list[PoisonControl]:
        """Return poison-control centres, optionally filtered by scope."""
        sql = "SELECT * FROM poison_controls"
        params: list[str] = []
        if scope is not None:
            sql += " WHERE scope = ?"
            params.append(scope)
        sql += " ORDER BY id"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [_serde.poison_control_from_row(row) for row in rows]

    def get_metadata(self) -> StorageMetadata:
        """Return metadata describing the built database.

        Raises:
            StorageError: If the metadata table is missing required keys.
        """
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT key, value FROM _metadata").fetchall()
        raw = {row["key"]: json.loads(row["value"]) for row in rows}
        try:
            return StorageMetadata(
                built_at=datetime.fromisoformat(raw["built_at"]),
                snapshot_versions={
                    fn: date.fromisoformat(d) for fn, d in raw["snapshot_versions"].items()
                },
                record_counts=raw["record_counts"],
            )
        except KeyError as exc:
            raise StorageError(f"Database metadata is missing key {exc}") from exc
