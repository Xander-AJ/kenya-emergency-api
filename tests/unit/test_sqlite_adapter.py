"""Unit tests for the SQLite storage adapter."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from kenya_emergency.core.exceptions import DataNotFoundError, StorageError
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.storage import SQLiteAdapter, StorageMetadata


def test_lazy_build_triggers_when_db_missing(tmp_path: Path, snapshot_dir: Path) -> None:
    """A missing DB is built on construction when a snapshot_dir is supplied."""
    db_path = tmp_path / "lazy.db"
    assert not db_path.exists()

    adapter = SQLiteAdapter(db_path, snapshot_dir=snapshot_dir, auto_build=True)

    assert db_path.exists()
    assert len(adapter.list_counties()) == 2


def test_missing_db_without_autobuild_raises(tmp_path: Path) -> None:
    """A missing DB with auto_build disabled raises StorageError."""
    with pytest.raises(StorageError):
        SQLiteAdapter(tmp_path / "missing.db", auto_build=False)


def test_read_methods_return_typed_instances(built_db: Path) -> None:
    """Every read method reconstructs the correct model type."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    assert isinstance(adapter.get_county("047"), County)
    counties = adapter.list_counties()
    assert counties and all(isinstance(c, County) for c in counties)

    contacts = adapter.get_emergency_contacts("047")
    assert contacts and all(isinstance(c, EmergencyContact) for c in contacts)

    nationals = adapter.list_national_numbers()
    assert nationals and all(isinstance(n, NationalNumber) for n in nationals)

    poisons = adapter.list_poison_controls()
    assert poisons and all(isinstance(p, PoisonControl) for p in poisons)

    assert isinstance(adapter.get_metadata(), StorageMetadata)


def test_emergency_contact_category_filter(built_db: Path) -> None:
    """Filtering by category narrows results; unfiltered returns all categories."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    all_contacts = adapter.get_emergency_contacts("047")
    assert len(all_contacts) == 2
    assert {c.category for c in all_contacts} == {
        ContactCategory.POLICE,
        ContactCategory.FIRE,
    }

    police_only = adapter.get_emergency_contacts("047", category=ContactCategory.POLICE)
    assert len(police_only) == 1
    assert police_only[0].category is ContactCategory.POLICE


def test_get_county_unknown_raises(built_db: Path) -> None:
    """An unknown county code raises DataNotFoundError."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    with pytest.raises(DataNotFoundError):
        adapter.get_county("099")


def test_list_poison_controls_scope_filter(built_db: Path) -> None:
    """The scope filter selects only matching centres."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    assert len(adapter.list_poison_controls(scope="national")) == 1
    assert adapter.list_poison_controls(scope="regional") == []


def test_get_metadata_shape(built_db: Path) -> None:
    """Metadata round-trips out of the _metadata table with the right shape."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    metadata = adapter.get_metadata()

    assert isinstance(metadata.built_at, datetime)
    assert metadata.record_counts == {
        "counties": 2,
        "emergency_contacts": 4,
        "national_numbers": 2,
        "poison_controls": 1,
    }
    assert "counties_v1.json" in metadata.snapshot_versions
