"""National number model.

A nationwide service reachable by a short dialer code (e.g., "999", "112",
"1199"), optionally with full-format alternate phone lines.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from kenya_emergency.models.emergency_contact import ContactCategory
from kenya_emergency.models.phone import KenyanPhoneNumber
from kenya_emergency.models.provenance import Provenance


class NationalNumber(BaseModel):
    """A national emergency service identified by its short dialer code.

    v1 scope: ``short_code`` is a 3-5 digit dialer code, *not* a phone number,
    so it is stored as a plain validated string. Full-format alternates (such as
    the Kenya Red Cross +254 lines) go in ``alternate_numbers`` and are
    normalized to E.164.

    Attributes:
        service_name: Name of the service (e.g., "Police Emergency").
        short_code: 3-5 digit dialer code (e.g., "999", "112", "1199").
        alternate_numbers: Optional full-format alternate numbers (E.164).
        category: Service classification.
        description: Human-readable description of the service.
        provenance: Required audit trail for this record.
    """

    service_name: str
    short_code: str = Field(pattern=r"^\d{3,5}$")
    alternate_numbers: list[KenyanPhoneNumber] = Field(default_factory=list)
    category: ContactCategory
    description: str
    provenance: Provenance
