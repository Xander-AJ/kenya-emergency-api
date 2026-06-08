"""County routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from kenya_emergency.api.dependencies import get_service
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.services.emergency_service import EmergencyService

router = APIRouter(prefix="/counties", tags=["counties"])


@router.get("", response_model=list[County])
def list_counties(service: EmergencyService = Depends(get_service)) -> list[County]:
    """Return all 47 counties, ordered by code. Raises nothing."""
    return service.counties()


@router.get("/by-name/{name}", response_model=County)
def get_county_by_name(name: str, service: EmergencyService = Depends(get_service)) -> County:
    """Return a county matched by name (case-insensitive).

    Raises ``DataNotFoundError`` (404) if no county name matches.
    """
    return service.county_by_name(name)


@router.get("/{code}", response_model=County)
def get_county(code: str, service: EmergencyService = Depends(get_service)) -> County:
    """Return one county by code (``"47"`` or ``"047"``).

    Raises ``ValueError`` (400) for a malformed/out-of-range code and
    ``DataNotFoundError`` (404) for a well-formed but absent code.
    """
    return service.county(code)


@router.get("/{code}/contacts", response_model=list[EmergencyContact])
def get_county_contacts(
    code: str,
    category: ContactCategory | None = Query(default=None, description="Optional category filter."),
    service: EmergencyService = Depends(get_service),
) -> list[EmergencyContact]:
    """Return a county's emergency contacts, optionally filtered by category.

    Raises ``ValueError`` (400) for a malformed code or unknown category, and
    returns an empty list for a valid county with no contacts.
    """
    return service.contacts_for_county(code, category)
