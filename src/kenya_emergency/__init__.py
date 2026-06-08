"""kenya-emergency-api: Kenyan emergency contact data as a library and an API.

This package exposes a single transport-agnostic service layer that can be
consumed directly from Python or served over HTTP via FastAPI.

The canonical entry point is :class:`EmergencyService`::

    from kenya_emergency import EmergencyService, ContactCategory

    service = EmergencyService()
    service.contacts_for_county("047", ContactCategory.FIRE)
"""

from kenya_emergency.api.app import create_app
from kenya_emergency.models import (
    ContactCategory,
    County,
    EmergencyContact,
    EmergencyOverview,
    KenyanPhoneNumber,
    NationalNumber,
    PoisonControl,
    Provenance,
    VerificationMethod,
)
from kenya_emergency.services.emergency_service import EmergencyService
from kenya_emergency.version import __version__

__all__ = [
    "ContactCategory",
    "County",
    "EmergencyContact",
    "EmergencyOverview",
    "EmergencyService",
    "KenyanPhoneNumber",
    "NationalNumber",
    "PoisonControl",
    "Provenance",
    "VerificationMethod",
    "__version__",
    "create_app",
]
