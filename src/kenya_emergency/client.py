"""Public client surface — re-exports EmergencyService for backwards compat.

The canonical import is ``from kenya_emergency import EmergencyService``; this
module is kept because its path appears in the original project layout.
"""

from kenya_emergency.services.emergency_service import EmergencyService

__all__ = ["EmergencyService"]
