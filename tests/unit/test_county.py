"""Unit tests for the County model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from kenya_emergency.models.county import County
from kenya_emergency.models.provenance import Provenance


def test_valid_construction(sample_provenance: Provenance) -> None:
    """A county with a valid code and required fields constructs cleanly."""
    county = County(
        code="047",
        name="Nairobi",
        capital="Nairobi City",
        region="Nairobi Metropolitan",
        provenance=sample_provenance,
    )

    assert county.code == "047"
    assert county.region == "Nairobi Metropolitan"


def test_region_is_optional(sample_provenance: Provenance) -> None:
    """region may be omitted in v1."""
    county = County(
        code="001",
        name="Mombasa",
        capital="Mombasa City",
        provenance=sample_provenance,
    )

    assert county.region is None


@pytest.mark.parametrize("code", ["48", "100", "abc", "000", "048", "1"])
def test_invalid_code_patterns_rejected(code: str, sample_provenance: Provenance) -> None:
    """Codes outside the 001-047 pattern/range are rejected."""
    with pytest.raises(ValidationError):
        County(
            code=code,
            name="Somewhere",
            capital="Somewhere City",
            provenance=sample_provenance,
        )


def test_missing_provenance_fails() -> None:
    """A county without provenance cannot be constructed."""
    with pytest.raises(ValidationError):
        County(code="001", name="Mombasa", capital="Mombasa City")  # type: ignore[call-arg]
