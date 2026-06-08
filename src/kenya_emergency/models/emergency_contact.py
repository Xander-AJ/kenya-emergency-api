"""Emergency contact model.

A county-scoped emergency contact: a named service in a specific county with one
or more dialable phone numbers, classified by category.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from kenya_emergency.models.county import CountyCode
from kenya_emergency.models.phone import KenyanPhoneNumber
from kenya_emergency.models.provenance import Provenance


class ContactCategory(StrEnum):
    """The kind of emergency service a contact represents.

    Shared across :class:`EmergencyContact` and
    :class:`~kenya_emergency.models.national_number.NationalNumber`.
    """

    POLICE = "police"
    FIRE = "fire"
    AMBULANCE = "ambulance"
    REDCROSS = "redcross"
    GBV = "gbv"
    CHILD_HELPLINE = "child_helpline"
    GENERAL = "general"


class EmergencyContact(BaseModel):
    """A county-level emergency contact.

    v1 scope: every contact belongs to exactly one county and carries at least
    one full phone number (short dialer codes live on
    :class:`~kenya_emergency.models.national_number.NationalNumber`).

    Attributes:
        county_code: County this contact serves, "001"-"047".
        category: Service classification.
        name: Service name (e.g., "Nairobi County Fire Brigade").
        phone_numbers: One or more numbers, normalized to E.164.
        notes: Optional free-form context.
        provenance: Required audit trail for this record.
    """

    county_code: CountyCode
    category: ContactCategory
    name: str
    phone_numbers: list[KenyanPhoneNumber] = Field(min_length=1)
    notes: str | None = None
    provenance: Provenance
