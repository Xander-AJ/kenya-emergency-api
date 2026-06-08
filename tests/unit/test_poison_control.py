"""Unit tests for the PoisonControl model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.models.provenance import Provenance


def test_national_scope_without_region_accepted(sample_provenance: Provenance) -> None:
    """A national centre needs no region and normalizes its phone numbers."""
    centre = PoisonControl(
        name="KEMRI Poisons Information Centre",
        phone_numbers=["020 222 2222"],
        short_codes=["1199"],
        hours="24/7",
        scope="national",
        provenance=sample_provenance,
    )

    assert centre.scope == "national"
    assert centre.region is None
    assert centre.phone_numbers == ["+254202222222"]


def test_regional_scope_without_region_rejected(sample_provenance: Provenance) -> None:
    """A regional centre must name the region it serves."""
    with pytest.raises(ValidationError):
        PoisonControl(
            name="Coast Regional Poisons Centre",
            phone_numbers=["0712345678"],
            scope="regional",
            provenance=sample_provenance,
        )


def test_regional_scope_with_region_accepted(sample_provenance: Provenance) -> None:
    """A regional centre with a region constructs cleanly."""
    centre = PoisonControl(
        name="Coast Regional Poisons Centre",
        phone_numbers=["0712345678"],
        scope="regional",
        region="Coast",
        provenance=sample_provenance,
    )

    assert centre.region == "Coast"


@pytest.mark.parametrize("short_code", ["99", "123456", "12a"])
def test_invalid_short_codes_rejected(short_code: str, sample_provenance: Provenance) -> None:
    """short_codes must each be 3-5 digits."""
    with pytest.raises(ValidationError):
        PoisonControl(
            name="KEMRI Poisons Information Centre",
            phone_numbers=["0712345678"],
            short_codes=[short_code],
            scope="national",
            provenance=sample_provenance,
        )
