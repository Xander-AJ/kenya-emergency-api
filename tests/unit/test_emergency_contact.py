"""Unit tests for the EmergencyContact model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.provenance import Provenance


def test_valid_construction(sample_provenance: Provenance) -> None:
    """A valid contact normalizes its phone numbers to E.164."""
    contact = EmergencyContact(
        county_code="047",
        category=ContactCategory.FIRE,
        name="Nairobi County Fire Brigade",
        phone_numbers=["020 222 2222"],
        provenance=sample_provenance,
    )

    assert contact.phone_numbers == ["+254202222222"]
    assert contact.category is ContactCategory.FIRE


def test_empty_phone_numbers_rejected(sample_provenance: Provenance) -> None:
    """At least one phone number is required."""
    with pytest.raises(ValidationError):
        EmergencyContact(
            county_code="047",
            category=ContactCategory.FIRE,
            name="Nairobi County Fire Brigade",
            phone_numbers=[],
            provenance=sample_provenance,
        )


def test_category_coerced_from_string(sample_provenance: Provenance) -> None:
    """A plain string value is coerced into the ContactCategory enum."""
    contact = EmergencyContact(
        county_code="047",
        category="police",  # type: ignore[arg-type]
        name="Nairobi Central Police Station",
        phone_numbers=["0712345678"],
        provenance=sample_provenance,
    )

    assert contact.category is ContactCategory.POLICE


def test_invalid_county_code_rejected(sample_provenance: Provenance) -> None:
    """county_code uses the same validation as County.code."""
    with pytest.raises(ValidationError):
        EmergencyContact(
            county_code="048",
            category=ContactCategory.POLICE,
            name="Nowhere Police",
            phone_numbers=["0712345678"],
            provenance=sample_provenance,
        )
