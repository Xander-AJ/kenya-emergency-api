"""End-to-end tests: EmergencyService over the real SQLite adapter."""

from __future__ import annotations

from pathlib import Path

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.overview import EmergencyOverview
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.services import EmergencyService
from kenya_emergency.storage import SQLiteAdapter, StorageMetadata


def _service(built_db: Path) -> EmergencyService:
    return EmergencyService(adapter=SQLiteAdapter(built_db, auto_build=False))


def test_every_public_method_against_built_db(built_db: Path) -> None:
    """Walk the whole public surface and assert correct types / non-empty results."""
    service = _service(built_db)

    counties = service.counties()
    assert len(counties) == 2
    assert all(isinstance(c, County) for c in counties)

    assert isinstance(service.county("47"), County)
    assert service.county_by_name("nairobi").code == "047"

    contacts = service.contacts_for_county("047")
    assert len(contacts) == 2
    assert all(isinstance(c, EmergencyContact) for c in contacts)
    assert len(service.contacts_for_county("047", "police")) == 1
    assert len(service.contacts_by_county_name("Mombasa")) == 2

    nationals = service.national_numbers()
    assert len(nationals) == 2
    assert all(isinstance(n, NationalNumber) for n in nationals)

    police = service.police_emergency()
    assert police is not None and police.short_code == "999"
    assert service.ambulance_emergency() is None  # fixtures have no ambulance entry

    poisons = service.poison_controls(scope="national")
    assert len(poisons) == 1
    assert all(isinstance(p, PoisonControl) for p in poisons)

    assert isinstance(service.metadata(), StorageMetadata)


def test_overview_round_trips_through_json(built_db: Path) -> None:
    """An EmergencyOverview survives a model_dump_json / model_validate_json cycle."""
    service = _service(built_db)

    overview = service.emergency_overview("Nairobi")
    assert overview.county.code == "047"
    assert set(overview.contacts_by_category) == {ContactCategory.POLICE, ContactCategory.FIRE}

    restored = EmergencyOverview.model_validate_json(overview.model_dump_json())
    assert restored == overview
