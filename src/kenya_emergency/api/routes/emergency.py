"""National emergency-number and overview routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from kenya_emergency.api.dependencies import get_service
from kenya_emergency.core.exceptions import DataNotFoundError
from kenya_emergency.models.emergency_contact import ContactCategory
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.overview import EmergencyOverview
from kenya_emergency.services.emergency_service import EmergencyService

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.get("/national", response_model=list[NationalNumber])
def list_national_numbers(
    category: ContactCategory | None = Query(default=None, description="Optional category filter."),
    service: EmergencyService = Depends(get_service),
) -> list[NationalNumber]:
    """Return national emergency numbers, optionally filtered by category.

    Raises ``ValueError`` (400) for an unknown category.
    """
    return service.national_numbers(category)


@router.get("/national/police", response_model=NationalNumber)
def police_emergency(
    service: EmergencyService = Depends(get_service),
) -> NationalNumber:
    """Return the police national number.

    Raises ``DataNotFoundError`` (404) if no police entry exists.
    """
    result = service.police_emergency()
    if result is None:
        raise DataNotFoundError("No police national emergency number is available")
    return result


@router.get("/national/ambulance", response_model=NationalNumber)
def ambulance_emergency(
    service: EmergencyService = Depends(get_service),
) -> NationalNumber:
    """Return the ambulance national number.

    Raises ``DataNotFoundError`` (404) if no ambulance entry exists.
    """
    result = service.ambulance_emergency()
    if result is None:
        raise DataNotFoundError("No ambulance national emergency number is available")
    return result


@router.get("/overview/{code_or_name}", response_model=EmergencyOverview)
def emergency_overview(
    code_or_name: str, service: EmergencyService = Depends(get_service)
) -> EmergencyOverview:
    """Return a one-call overview for a county (by code or name).

    Bundles the county, its contacts grouped by category, all national numbers,
    and national poison-control centres. Raises ``DataNotFoundError`` (404) if
    the value matches neither a county code nor a name.
    """
    return service.emergency_overview(code_or_name)
