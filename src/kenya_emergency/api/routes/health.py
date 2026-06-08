"""Health and metadata routes.

``/health`` is a storage-free liveness probe mounted at the root. ``/metadata``
is the readiness probe (it touches storage) and is mounted under ``/v1``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from kenya_emergency.api.dependencies import get_service
from kenya_emergency.services.emergency_service import EmergencyService
from kenya_emergency.storage.base import StorageMetadata
from kenya_emergency.version import __version__

#: Root-level liveness router (no ``/v1`` prefix, by convention).
router = APIRouter(tags=["meta"])

#: Metadata router, mounted under ``/v1`` by :func:`create_app`.
metadata_router = APIRouter(tags=["meta"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness check.

    Returns a static ``{"status": "ok", "version": ...}`` without touching
    storage, so it stays green even if the database is unavailable. Raises
    nothing.
    """
    return {"status": "ok", "version": __version__}


@metadata_router.get("/metadata", response_model=StorageMetadata)
def metadata(service: EmergencyService = Depends(get_service)) -> StorageMetadata:
    """Readiness check: dataset build time, snapshot versions, and row counts.

    This touches storage (and triggers a lazy build on first use). Raises
    ``StorageError`` (503) if storage is unavailable.
    """
    return service.metadata()
