"""Unit tests for the NationalNumber model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kenya_emergency.models.emergency_contact import ContactCategory
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.provenance import Provenance


def test_valid_construction(sample_provenance: Provenance) -> None:
    """A valid national number constructs with an empty alternates list by default."""
    number = NationalNumber(
        service_name="Police Emergency",
        short_code="999",
        category=ContactCategory.POLICE,
        description="National police emergency line.",
        provenance=sample_provenance,
    )

    assert number.short_code == "999"
    assert number.alternate_numbers == []


@pytest.mark.parametrize("short_code", ["99", "123456", "12a", "", "1 2 3"])
def test_invalid_short_code_rejected(short_code: str, sample_provenance: Provenance) -> None:
    """short_code must be 3-5 digits."""
    with pytest.raises(ValidationError):
        NationalNumber(
            service_name="Bad Service",
            short_code=short_code,
            category=ContactCategory.GENERAL,
            description="Invalid short code.",
            provenance=sample_provenance,
        )


def test_alternate_numbers_normalize_to_e164(sample_provenance: Provenance) -> None:
    """Full-format alternates are normalized to E.164."""
    number = NationalNumber(
        service_name="Kenya Red Cross",
        short_code="1199",
        alternate_numbers=["020 222 2222", "0712345678"],
        category=ContactCategory.REDCROSS,
        description="Kenya Red Cross emergency operations.",
        provenance=sample_provenance,
    )

    assert number.alternate_numbers == ["+254202222222", "+254712345678"]
