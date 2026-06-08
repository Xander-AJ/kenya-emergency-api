"""Unit tests for EmergencyService and its input normalizers."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Literal

import pytest

from kenya_emergency.core.exceptions import DataNotFoundError
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.models.provenance import Provenance, VerificationMethod
from kenya_emergency.services import EmergencyService, _normalize
from kenya_emergency.storage.base import StorageAdapter, StorageMetadata

_PROV = Provenance(
    source="Test",
    last_verified_at=date(2026, 1, 1),
    verification_method=VerificationMethod.MANUAL_CALL,
)


def _county(code: str, name: str) -> County:
    return County(code=code, name=name, capital=name, provenance=_PROV)


def _contact(code: str, category: ContactCategory, name: str) -> EmergencyContact:
    return EmergencyContact(
        county_code=code,
        category=category,
        name=name,
        phone_numbers=["0712345678"],
        provenance=_PROV,
    )


def _national(name: str, short_code: str, category: ContactCategory) -> NationalNumber:
    return NationalNumber(
        service_name=name,
        short_code=short_code,
        category=category,
        description=name,
        provenance=_PROV,
    )


def _poison(name: str, scope: Literal["national", "regional"], region: str | None) -> PoisonControl:
    return PoisonControl(
        name=name,
        phone_numbers=["0712345678"],
        scope=scope,
        region=region,
        provenance=_PROV,
    )


class FakeAdapter(StorageAdapter):
    """In-memory StorageAdapter with the same filtering semantics as SQLite."""

    def __init__(self) -> None:
        self._counties = [_county("047", "Nairobi"), _county("001", "Mombasa")]
        self._contacts = [
            _contact("047", ContactCategory.POLICE, "Nairobi Police"),
            _contact("047", ContactCategory.FIRE, "Nairobi Fire"),
            _contact("001", ContactCategory.POLICE, "Mombasa Police"),
        ]
        self._nationals = [
            _national("Police Emergency", "999", ContactCategory.POLICE),
            _national("Kenya Red Cross", "1199", ContactCategory.REDCROSS),
        ]
        self._poisons = [
            _poison("National Poison Centre", "national", None),
            _poison("Coast Poison Centre", "regional", "Coast"),
        ]

    def get_county(self, code: str) -> County:
        for county in self._counties:
            if county.code == code:
                return county
        raise DataNotFoundError(f"No county with code {code!r}")

    def list_counties(self) -> list[County]:
        return list(self._counties)

    def get_emergency_contacts(
        self, county_code: str, category: ContactCategory | None = None
    ) -> list[EmergencyContact]:
        return [
            c
            for c in self._contacts
            if c.county_code == county_code and (category is None or c.category == category)
        ]

    def list_national_numbers(
        self, category: ContactCategory | None = None
    ) -> list[NationalNumber]:
        return [n for n in self._nationals if category is None or n.category == category]

    def list_poison_controls(
        self, scope: Literal["national", "regional"] | None = None
    ) -> list[PoisonControl]:
        return [p for p in self._poisons if scope is None or p.scope == scope]

    def get_metadata(self) -> StorageMetadata:
        return StorageMetadata(
            built_at=datetime(2026, 1, 1, tzinfo=UTC),
            snapshot_versions={"counties_v1.json": date(2026, 1, 1)},
            record_counts={"counties": 2},
        )


@pytest.fixture
def service() -> EmergencyService:
    """An EmergencyService backed by the in-memory FakeAdapter."""
    return EmergencyService(adapter=FakeAdapter())


# --- normalizers ------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("47", "047"), (" 47 ", "047"), ("047", "047"), ("7", "007")],
)
def test_normalize_county_code(raw: str, expected: str) -> None:
    assert _normalize.normalize_county_code(raw) == expected


@pytest.mark.parametrize("raw", ["fire", "FIRE", "Fire", " fire "])
def test_normalize_category_case_insensitive(raw: str) -> None:
    assert _normalize.normalize_category(raw) is ContactCategory.FIRE


def test_normalize_category_passthrough_and_none() -> None:
    assert _normalize.normalize_category(None) is None
    assert _normalize.normalize_category(ContactCategory.POLICE) is ContactCategory.POLICE


def test_normalize_category_invalid_raises() -> None:
    with pytest.raises(ValueError, match="unknown contact category"):
        _normalize.normalize_category("fire brigade")


@pytest.mark.parametrize("raw", ["abc", "47.0", "048", "000", "999", "0470"])
def test_normalize_county_code_invalid_raises(raw: str) -> None:
    """Malformed shape and out-of-range codes raise ValueError, not DataNotFoundError."""
    with pytest.raises(ValueError, match="Invalid county code"):
        _normalize.normalize_county_code(raw)


def test_normalize_county_name() -> None:
    assert _normalize.normalize_county_name("  Nairobi ") == "nairobi"


# --- counties ---------------------------------------------------------------


def test_county_normalizes_short_code(service: EmergencyService) -> None:
    assert service.county("47").name == "Nairobi"


def test_county_absent_but_valid_shape_raises_not_found(service: EmergencyService) -> None:
    """A well-formed code with no record raises DataNotFoundError."""
    with pytest.raises(DataNotFoundError):
        service.county("046")


def test_county_malformed_raises_value_error(service: EmergencyService) -> None:
    """A code we can't parse raises ValueError, not DataNotFoundError."""
    with pytest.raises(ValueError, match="Invalid county code"):
        service.county("999")


def test_county_by_name_case_insensitive(service: EmergencyService) -> None:
    assert service.county_by_name("NAIROBI").code == "047"


def test_county_by_name_unknown_raises(service: EmergencyService) -> None:
    with pytest.raises(DataNotFoundError):
        service.county_by_name("Atlantis")


# --- contacts ---------------------------------------------------------------


def test_contacts_accepts_string_category(service: EmergencyService) -> None:
    contacts = service.contacts_for_county("47", "police")
    assert len(contacts) == 1
    assert contacts[0].category is ContactCategory.POLICE


def test_contacts_accepts_enum_category(service: EmergencyService) -> None:
    contacts = service.contacts_for_county("47", ContactCategory.FIRE)
    assert len(contacts) == 1
    assert contacts[0].category is ContactCategory.FIRE


def test_contacts_none_returns_all_categories(service: EmergencyService) -> None:
    contacts = service.contacts_for_county("47")
    assert {c.category for c in contacts} == {ContactCategory.POLICE, ContactCategory.FIRE}


def test_contacts_by_county_name(service: EmergencyService) -> None:
    contacts = service.contacts_by_county_name("nairobi", "police")
    assert len(contacts) == 1


# --- national numbers -------------------------------------------------------


def test_national_numbers_filter(service: EmergencyService) -> None:
    assert len(service.national_numbers()) == 2
    police = service.national_numbers("police")
    assert len(police) == 1
    assert police[0].category is ContactCategory.POLICE


def test_police_emergency_present(service: EmergencyService) -> None:
    police = service.police_emergency()
    assert police is not None
    assert police.short_code == "999"


def test_ambulance_emergency_absent_returns_none(service: EmergencyService) -> None:
    assert service.ambulance_emergency() is None


# --- poison control ---------------------------------------------------------


def test_poison_controls_scope_filter(service: EmergencyService) -> None:
    assert len(service.poison_controls()) == 2
    national = service.poison_controls(scope="national")
    assert len(national) == 1
    assert national[0].scope == "national"


# --- overview & metadata ----------------------------------------------------


def test_emergency_overview_by_code(service: EmergencyService) -> None:
    overview = service.emergency_overview("47")
    assert overview.county.code == "047"
    assert set(overview.contacts_by_category) == {ContactCategory.POLICE, ContactCategory.FIRE}
    assert len(overview.national_numbers) == 2
    assert all(p.scope == "national" for p in overview.poison_controls)


def test_emergency_overview_by_name(service: EmergencyService) -> None:
    overview = service.emergency_overview("Mombasa")
    assert overview.county.code == "001"
    assert set(overview.contacts_by_category) == {ContactCategory.POLICE}


def test_emergency_overview_unknown_raises(service: EmergencyService) -> None:
    with pytest.raises(DataNotFoundError):
        service.emergency_overview("Atlantis")


def test_metadata(service: EmergencyService) -> None:
    assert service.metadata().record_counts == {"counties": 2}
