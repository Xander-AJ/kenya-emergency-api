"""Unit tests for the KenyanPhoneNumber type."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from kenya_emergency.models.phone import KenyanPhoneNumber


class _Model(BaseModel):
    """Minimal model used to drive validation of the phone type."""

    number: KenyanPhoneNumber


def test_valid_mobile_normalizes_to_e164() -> None:
    """A valid Kenyan mobile number is normalized to E.164."""
    assert _Model(number="0712345678").number == "+254712345678"


def test_valid_landline_normalizes_to_e164() -> None:
    """A valid Kenyan landline number is normalized to E.164."""
    assert _Model(number="0202222222").number == "+254202222222"


@pytest.mark.parametrize(
    "raw",
    [
        "0202222222",
        "020 222 2222",
        "+254 20 222 2222",
        "020-222-2222",
        "+254202222222",
    ],
)
def test_normalization_across_input_variations(raw: str) -> None:
    """Common formatting variations all collapse to the same E.164 string."""
    assert _Model(number=raw).number == "+254202222222"


def test_short_code_rejected() -> None:
    """A short dialer code like '999' is not a parseable phone number."""
    with pytest.raises(ValidationError):
        _Model(number="999")


def test_invalid_input_rejected() -> None:
    """Garbage input is rejected."""
    with pytest.raises(ValidationError):
        _Model(number="not-a-number")
