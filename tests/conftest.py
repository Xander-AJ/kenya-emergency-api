"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path

import pytest

from kenya_emergency.models.provenance import Provenance, VerificationMethod
from kenya_emergency.storage import build_database

#: Location of the small, real-shape JSON snapshots used to build a test DB.
SNAPSHOT_DIR = Path(__file__).resolve().parent / "data" / "snapshots"


@pytest.fixture
def sample_provenance() -> Provenance:
    """A valid Provenance instance for composing domain-model test fixtures."""
    return Provenance(
        source="Kenya National Disaster Operations Centre",
        source_url="https://www.ndoc.go.ke/",  # type: ignore[arg-type]
        last_verified_at=date(2026, 1, 15),
        verification_method=VerificationMethod.MANUAL_CALL,
        notes=None,
    )


@pytest.fixture
def snapshot_dir() -> Path:
    """Path to the test JSON snapshot fixtures."""
    return SNAPSHOT_DIR


@pytest.fixture
def built_db(tmp_path: Path, snapshot_dir: Path) -> Iterator[Path]:
    """Build a fresh SQLite database in tmp_path from the fixtures and yield its path."""
    db_path = tmp_path / "kenya_emergency.db"
    build_database(snapshot_dir, db_path)
    yield db_path
