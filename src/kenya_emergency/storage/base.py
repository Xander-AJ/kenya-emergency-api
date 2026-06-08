"""Storage adapter interface.

Defines the transport-agnostic contract every backend must satisfy. All methods
are synchronous for v1; any async wrapping belongs at the API layer, not here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl


class StorageMetadata(BaseModel):
    """Describes a built database: when it was built and what it contains.

    Attributes:
        built_at: UTC timestamp of when the database was built.
        snapshot_versions: Maps each source snapshot filename to the most recent
            ``provenance.last_verified_at`` date among its records. Files that
            contributed zero records are omitted.
        record_counts: Maps each table name to its row count.
    """

    built_at: datetime
    snapshot_versions: dict[str, date]
    record_counts: dict[str, int]


class StorageAdapter(ABC):
    """Read interface over the emergency-data store.

    Implementations return fully-validated Pydantic model instances; callers never
    see raw rows. All methods are synchronous.
    """

    @abstractmethod
    def get_county(self, code: str) -> County:
        """Return the county with the given code.

        Args:
            code: County code, "001"-"047".

        Returns:
            The matching :class:`County`.

        Raises:
            DataNotFoundError: If no county has that code.
        """

    @abstractmethod
    def list_counties(self) -> list[County]:
        """Return all counties, ordered by code."""

    @abstractmethod
    def get_emergency_contacts(
        self, county_code: str, category: ContactCategory | None = None
    ) -> list[EmergencyContact]:
        """Return emergency contacts for a county, optionally filtered by category.

        Args:
            county_code: County code to scope the query to.
            category: If given, return only contacts in this category.

        Returns:
            Matching contacts (possibly empty).
        """

    @abstractmethod
    def list_national_numbers(
        self, category: ContactCategory | None = None
    ) -> list[NationalNumber]:
        """Return national numbers, optionally filtered by category."""

    @abstractmethod
    def list_poison_controls(
        self, scope: Literal["national", "regional"] | None = None
    ) -> list[PoisonControl]:
        """Return poison-control centres, optionally filtered by scope."""

    @abstractmethod
    def get_metadata(self) -> StorageMetadata:
        """Return metadata describing the built database."""
