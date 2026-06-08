"""Poison-control routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query

from kenya_emergency.api.dependencies import get_service
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.services.emergency_service import EmergencyService

router = APIRouter(prefix="/poison", tags=["poison"])


@router.get("/control", response_model=list[PoisonControl])
def list_poison_controls(
    scope: Literal["national", "regional"] | None = Query(
        default=None, description="Optional scope filter."
    ),
    service: EmergencyService = Depends(get_service),
) -> list[PoisonControl]:
    """Return poison-control centres, optionally filtered by scope. Raises nothing."""
    return service.poison_controls(scope)
