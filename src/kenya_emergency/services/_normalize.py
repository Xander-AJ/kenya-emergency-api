"""Input normalization for the service layer.

These helpers turn forgiving human input (``"47"``, ``"Fire"``, ``" Nairobi "``)
into the canonical forms the storage layer expects. They normalize shape only;
existence checks (and the resulting :class:`DataNotFoundError`) happen when the
normalized value is looked up.
"""

from __future__ import annotations

from kenya_emergency.models.emergency_contact import ContactCategory


def normalize_county_code(value: str) -> str:
    """Normalize a county code for lookup.

    Strips surrounding whitespace and left-pads with zeros to three characters,
    so ``"47"``, ``" 47 "``, and ``"047"`` all become ``"047"``.

    Normalization is shape only, not existence: a well-formed code with no
    matching record is returned and surfaces as :class:`DataNotFoundError` at
    lookup time.

    Args:
        value: Raw county-code input.

    Returns:
        The normalized county code.
    """
    return value.strip().zfill(3)


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
        raise ValueError(
            f"unknown contact category {value!r}; expected one of: {valid}"
        ) from None
