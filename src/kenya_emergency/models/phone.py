"""Kenyan phone number type.

Kenyan emergency data is saturated with phone numbers in inconsistent formats.
This module defines :data:`KenyanPhoneNumber`, a reusable pydantic type that
parses, validates, and normalizes any Kenyan number to canonical E.164 form.

v1 scope: only full, dialable phone numbers (mobile and landline) are modeled
here. Short dialer codes such as "999" or "112" are *not* phone numbers; they
are stored as plain strings on :class:`~kenya_emergency.models.national_number.NationalNumber`
and :class:`~kenya_emergency.models.poison_control.PoisonControl`.
"""

from __future__ import annotations

from typing import Annotated

import phonenumbers
from pydantic import AfterValidator


def normalize_kenyan_phone_number(value: str) -> str:
    """Parse, validate, and normalize a Kenyan phone number to E.164.

    Accepts common local and international input variations (for example
    ``"0202222222"``, ``"020 222 2222"``, ``"020-222-2222"``, and
    ``"+254 20 222 2222"``) and returns the canonical E.164 string such as
    ``"+254202222222"``.

    Args:
        value: The raw phone number string to normalize.

    Returns:
        The number formatted as E.164.

    Raises:
        ValueError: If the value cannot be parsed or is not a valid Kenyan
            number (which is how pydantic surfaces a validation failure).
    """
    try:
        parsed = phonenumbers.parse(value, "KE")
    except phonenumbers.NumberParseException as exc:
        raise ValueError(f"Could not parse {value!r} as a Kenyan phone number") from exc

    if not phonenumbers.is_valid_number(parsed):
        raise ValueError(f"{value!r} is not a valid Kenyan phone number")

    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


#: A ``str`` that is always stored in E.164 form. Assign any common Kenyan input
#: variation; pydantic normalizes it on validation.
KenyanPhoneNumber = Annotated[str, AfterValidator(normalize_kenyan_phone_number)]
