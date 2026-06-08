"""The public Python service surface.

:class:`EmergencyService` is the transport-agnostic API developers import
directly (``from kenya_emergency import EmergencyService``). It wraps a
:class:`StorageAdapter`, applies forgiving input normalization, and returns
fully-validated Pydantic models. The FastAPI layer wraps this same class.
"""

from __future__ import annotations

from typing import Literal

from kenya_emergency.core.config import Settings
from kenya_emergency.core.exceptions import ConfigurationError, DataNotFoundError
from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory, EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.overview import EmergencyOverview
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.services import _normalize
from kenya_emergency.storage.base import StorageAdapter, StorageMetadata
from kenya_emergency.storage.sqlite_adapter import SQLiteAdapter
from kenya_emergency.storage.supabase_adapter import SupabaseAdapter


class EmergencyService:
    """High-level read API over Kenyan emergency data.

    Methods are synchronous and return validated model instances. Lookups that
    cannot find a record raise :class:`DataNotFoundError`; malformed category
    strings raise :class:`ValueError`.
    """

    def __init__(
        self,
        adapter: StorageAdapter | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Create a service, building a default adapter if none is supplied.

        Args:
            adapter: A storage adapter to use directly. When ``None``, an adapter
                is constructed from ``settings.storage_adapter``.
            settings: Configuration to use. When ``None``, :class:`Settings` is
                instantiated from the environment/defaults.

        Raises:
            ConfigurationError: If the configured adapter is ``"supabase"`` but
                its URL or key is missing.
        """
        self._settings = settings if settings is not None else Settings()
        self._adapter = adapter if adapter is not None else self._build_adapter(self._settings)

    @staticmethod
    def _build_adapter(settings: Settings) -> StorageAdapter:
        """Construct the storage adapter named by ``settings.storage_adapter``."""
        if settings.storage_adapter == "sqlite":
            return SQLiteAdapter(
                db_path=settings.db_path,
                snapshot_dir=settings.snapshot_dir,
                auto_build=True,
            )
        if settings.supabase_url is None or settings.supabase_key is None:
            raise ConfigurationError(
                "storage_adapter='supabase' requires supabase_url and supabase_key"
            )
        return SupabaseAdapter(str(settings.supabase_url), settings.supabase_key)

    # --- counties -----------------------------------------------------------

    def counties(self) -> list[County]:
        """Return all counties, ordered by code."""
        return self._adapter.list_counties()

    def county(self, code: str) -> County:
        """Return a county by code.

        Args:
            code: County code in any common form (``"47"``, ``"047"``,
                whitespace-padded); normalized to three digits before lookup.

        Returns:
            The matching :class:`County`.

        Raises:
            DataNotFoundError: If no county has the (normalized) code.
        """
        return self._adapter.get_county(_normalize.normalize_county_code(code))

    def county_by_name(self, name: str) -> County:
        """Return a county by name, matched case-insensitively.

        Args:
            name: County name (e.g. ``"nairobi"``, ``"Nairobi"``); compared
                case-insensitively after stripping whitespace.

        Returns:
            The matching :class:`County`.

        Raises:
            DataNotFoundError: If no county name matches.
        """
        target = _normalize.normalize_county_name(name)
        for county in self._adapter.list_counties():
            if county.name.casefold() == target:
                return county
        raise DataNotFoundError(f"No county named {name!r}")

    # --- emergency contacts -------------------------------------------------

    def contacts_for_county(
        self, code: str, category: ContactCategory | str | None = None
    ) -> list[EmergencyContact]:
        """Return a county's emergency contacts, optionally filtered by category.

        Args:
            code: County code, normalized like :meth:`county`.
            category: Optional category filter, as a :class:`ContactCategory`, a
                case-insensitive string (e.g. ``"fire"``), or ``None`` for all.

        Returns:
            Matching contacts (empty if the county has none or does not exist).

        Raises:
            ValueError: If ``category`` is a string that names no known category.
        """
        return self._adapter.get_emergency_contacts(
            _normalize.normalize_county_code(code),
            _normalize.normalize_category(category),
        )

    def contacts_by_county_name(
        self, name: str, category: ContactCategory | str | None = None
    ) -> list[EmergencyContact]:
        """Return emergency contacts for a county identified by name.

        Args:
            name: County name, matched like :meth:`county_by_name`.
            category: Optional category filter, as in :meth:`contacts_for_county`.

        Returns:
            Matching contacts.

        Raises:
            DataNotFoundError: If no county name matches.
            ValueError: If ``category`` is a string that names no known category.
        """
        county = self.county_by_name(name)
        return self.contacts_for_county(county.code, category)

    # --- national numbers ---------------------------------------------------

    def national_numbers(
        self, category: ContactCategory | str | None = None
    ) -> list[NationalNumber]:
        """Return national emergency numbers, optionally filtered by category.

        Args:
            category: Optional category filter, as a :class:`ContactCategory`, a
                case-insensitive string, or ``None`` for all.

        Returns:
            Matching national numbers.

        Raises:
            ValueError: If ``category`` is a string that names no known category.
        """
        return self._adapter.list_national_numbers(_normalize.normalize_category(category))

    def police_emergency(self) -> NationalNumber | None:
        """Return the police national number, or ``None`` if not present.

        Convenience for the most common lookup. If several police entries exist,
        the first (by storage order) is returned.
        """
        numbers = self._adapter.list_national_numbers(ContactCategory.POLICE)
        return numbers[0] if numbers else None

    def ambulance_emergency(self) -> NationalNumber | None:
        """Return the ambulance national number, or ``None`` if not present.

        Convenience for a common lookup. If several ambulance entries exist, the
        first (by storage order) is returned.
        """
        numbers = self._adapter.list_national_numbers(ContactCategory.AMBULANCE)
        return numbers[0] if numbers else None

    # --- poison control -----------------------------------------------------

    def poison_controls(
        self, scope: Literal["national", "regional"] | None = None
    ) -> list[PoisonControl]:
        """Return poison-control centres, optionally filtered by scope.

        Args:
            scope: ``"national"``, ``"regional"``, or ``None`` for all.

        Returns:
            Matching poison-control centres.
        """
        return self._adapter.list_poison_controls(scope)

    # --- composite / use-case ----------------------------------------------

    def emergency_overview(self, code_or_name: str) -> EmergencyOverview:
        """Return everything about one place in a single call.

        Resolves ``code_or_name`` as a county code first, then by name, and
        assembles the county, its contacts grouped by category, all national
        numbers, and the national poison-control centres.

        Args:
            code_or_name: A county code (``"47"``/``"047"``) or name
                (``"Nairobi"``).

        Returns:
            A populated :class:`EmergencyOverview`.

        Raises:
            DataNotFoundError: If the value matches neither a code nor a name.
        """
        county = self._resolve_county(code_or_name)
        contacts = self.contacts_for_county(county.code)

        grouped: dict[ContactCategory, list[EmergencyContact]] = {}
        for contact in contacts:
            grouped.setdefault(contact.category, []).append(contact)

        return EmergencyOverview(
            county=county,
            contacts_by_category=grouped,
            national_numbers=self.national_numbers(),
            poison_controls=self.poison_controls(scope="national"),
        )

    def _resolve_county(self, code_or_name: str) -> County:
        """Resolve a county by code, falling back to name.

        A :class:`ValueError` from code normalization (the input is not a
        valid code shape, e.g. ``"Nairobi"``) is treated as "not a code" and
        falls through to a name lookup, as is a well-formed but absent code.
        """
        try:
            return self.county(code_or_name)
        except (DataNotFoundError, ValueError):
            return self.county_by_name(code_or_name)

    # --- metadata -----------------------------------------------------------

    def metadata(self) -> StorageMetadata:
        """Return metadata describing the underlying database."""
        return self._adapter.get_metadata()
