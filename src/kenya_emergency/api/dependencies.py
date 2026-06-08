"""FastAPI dependency providers.

The :class:`EmergencyService` is created lazily on first use and cached on
``app.state`` so it is reused across requests. Lazy construction keeps app
creation (and importing the module-level ``app``) free of storage side effects:
``/health`` never needs a database, and a misconfigured deployment fails on the
first data request rather than at import time.
"""

from __future__ import annotations

from fastapi import Request

from kenya_emergency.services.emergency_service import EmergencyService


def get_service(request: Request) -> EmergencyService:
    """Return the shared :class:`EmergencyService`, building it once on demand.

    Args:
        request: The incoming request, used to reach ``app.state``.

    Returns:
        The application's cached :class:`EmergencyService`.
    """
    service: EmergencyService | None = getattr(request.app.state, "service", None)
    if service is None:
        service = EmergencyService(settings=request.app.state.settings)
        request.app.state.service = service
    return service
