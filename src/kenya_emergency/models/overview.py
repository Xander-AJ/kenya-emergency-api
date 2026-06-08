"""Emergency overview: a one-call composite of everything about a place.

Aggregates a county with its emergency contacts (grouped by category), the
national emergency numbers, and the national poison-control centres. This is the
shape returned by :meth:`EmergencyService.emergency_overview`.
"""

from __future__ import annotations

from pydantic import BaseModel

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl


class EmergencyOverview(BaseModel):
    """Everything a caller needs to know about emergencies in one county.

    Attributes:
        county: The county this overview describes.
        contacts_by_category: County emergency contacts grouped by category.
            Only categories that have at least one contact are present.
        national_numbers: All national emergency numbers (apply everywhere).
        poison_controls: National-scope poison-control centres.
    """

    county: County
    contacts_by_category: dict[ContactCategory, list[EmergencyContact]]
    national_numbers: list[NationalNumber]
    poison_controls: list[PoisonControl]
