"""Supabase storage adapter (optional, install via the ``supabase`` extra).

Planned for v1.1. The class exists so the adapter surface and configuration wiring
are stable today, but every read method raises :class:`NotImplementedError`: v1
ships SQLite only. Use :class:`~kenya_emergency.storage.sqlite_adapter.SQLiteAdapter`
for now.
"""

from __future__ import annotations

from typing import Literal

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.storage.base import StorageAdapter, StorageMetadata

_NOT_IMPLEMENTED = "SupabaseAdapter is planned for v1.1 — use SQLiteAdapter for v1"


class SupabaseAdapter(StorageAdapter):
    """Supabase-backed adapter. v1.1; all reads currently raise NotImplementedError."""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        """Store connection settings for the future Supabase implementation.

        Args:
            supabase_url: Supabase project URL.
            supabase_key: Supabase API key.
        """
        self._supabase_url = supabase_url
        self._supabase_key = supabase_key

    def get_county(self, code: str) -> County:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list_counties(self) -> list[County]:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def get_emergency_contacts(
        self, county_code: str, category: ContactCategory | None = None
    ) -> list[EmergencyContact]:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list_national_numbers(
        self, category: ContactCategory | None = None
    ) -> list[NationalNumber]:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list_poison_controls(
        self, scope: Literal["national", "regional"] | None = None
    ) -> list[PoisonControl]:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def get_metadata(self) -> StorageMetadata:
        """Not implemented in v1."""
        raise NotImplementedError(_NOT_IMPLEMENTED)
