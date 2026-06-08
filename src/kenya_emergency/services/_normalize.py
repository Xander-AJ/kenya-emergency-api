"""Input normalization for the service layer.

These helpers turn forgiving human input (``"47"``, ``"Fire"``, ``" Nairobi "``)
into the canonical forms the storage layer expects. They normalize shape only;
existence checks (and the resulting :class:`DataNotFoundError`) happen when the
normalized value is looked up.
"""

from __future__ import annotations

import re

from kenya_emergency.models.emergency_contact import ContactCategory

#: Same syntactic shape as ``County.code``: three digits, leading zero, "0XY".
_COUNTY_CODE_PATTERN = re.compile(r"^0[0-4][0-9]$")


def normalize_county_code(value: str) -> str:
    """Normalize and validate a county code for lookup.

    Strips surrounding whitespace and left-pads with zeros to three characters,
    so ``"47"``, ``" 47 "``, and ``"047"`` all become ``"047"``. The result is
    then validated against the same rules as ``County.code`` (pattern
    ``^0[0-4][0-9]$`` and range 001-047).

    Validation is shape, not existence: a well-formed code with no matching
    record (e.g. ``"046"``) is returned and surfaces as :class:`DataNotFoundError`
    at lookup time. Malformed input (``"abc"``, ``"47.0"``, ``"048"``, ``"000"``)
    raises :class:`ValueError` here, mirroring how invalid category strings fail.

    Args:
        value: Raw county-code input.

    Returns:
        The normalized, validated county code.

    Raises:
        ValueError: If the input is not a valid Kenyan county code 001-047.
    """
    code = value.strip().zfill(3)
    if not _COUNTY_CODE_PATTERN.match(code) or not 1 <= int(code) <= 47:
        raise ValueError(
            f"Invalid county code: {value!r}. Expected a Kenyan county code "
            f"001-047 (e.g., '047' for Nairobi)."
        )
    return code


def normalize_county_name(value: str) -> str:
    """Normalize a county name for case-insensitive comparison.

    Strips surrounding whitespace and case-folds. Compare two normalized names
    for an exact, case-insensitive match.

    Args:
        value: Raw county-name input.

    Returns:
        The stripped, case-folded name.
    """
    return value.strip().casefold()


def normalize_category(value: ContactCategory | str | None) -> ContactCategory | None:
    """Normalize a contact-category argument to an enum (or ``None``).

    Accepts an existing :class:`ContactCategory`, ``None`` (meaning "no filter"),
    or a string matched case-insensitively against the category values
    (``"fire"``, ``"FIRE"``, ``"Fire"`` -> :attr:`ContactCategory.FIRE`).

    Args:
        value: The category as an enum, a string, or ``None``.

    Returns:
        The matching :class:`ContactCategory`, or ``None`` when ``value`` is
        ``None``.

    Raises:
        ValueError: If a string does not match any known category.
    """
    if value is None or isinstance(value, ContactCategory):
        return value
    key = value.strip().casefold()
    try:
        return ContactCategory(key)
    except ValueError:
        valid = ", ".join(category.value for category in ContactCategory)
        raise ValueError(f"unknown contact category {value!r}; expected one of: {valid}") from None
