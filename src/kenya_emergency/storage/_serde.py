"""Row <-> model conversion for the SQLite store.

This is the single place that knows how each domain model maps onto its table:
the parameterized ``INSERT`` statements (used by the builder) and the
``*_from_row`` reconstructors (used by the adapter) live together so the two
directions cannot drift apart. List-valued fields are JSON-encoded; the embedded
:class:`Provenance` is flattened into ``provenance_*`` columns.
"""

from __future__ import annotations

import json
from typing import Any

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import EmergencyContact
from kenya_emergency.models.national_number import NationalNumber
from kenya_emergency.models.poison_control import PoisonControl
from kenya_emergency.models.provenance import Provenance

# A typed alias for the sqlite3.Row-like mapping the adapter passes in. We only
# rely on ``__getitem__`` by column name, which sqlite3.Row supports.
Row = Any


def _provenance_params(provenance: Provenance) -> dict[str, Any]:
    """Flatten a Provenance into its ``provenance_*`` column values."""
    return {
        "provenance_source": provenance.source,
        "provenance_source_url": (
            str(provenance.source_url) if provenance.source_url is not None else None
        ),
        "provenance_last_verified_at": provenance.last_verified_at.isoformat(),
        "provenance_verification_method": provenance.verification_method.value,
        "provenance_notes": provenance.notes,
    }


def _provenance_from_row(row: Row) -> Provenance:
    """Reconstruct (and re-validate) a Provenance from its ``provenance_*`` columns."""
    return Provenance(
        source=row["provenance_source"],
        source_url=row["provenance_source_url"],
        last_verified_at=row["provenance_last_verified_at"],
        verification_method=row["provenance_verification_method"],
        notes=row["provenance_notes"],
    )


# --- counties ---------------------------------------------------------------

INSERT_COUNTY = """
INSERT INTO counties (
    code, name, capital, region,
    provenance_source, provenance_source_url, provenance_last_verified_at,
    provenance_verification_method, provenance_notes
) VALUES (
    :code, :name, :capital, :region,
    :provenance_source, :provenance_source_url, :provenance_last_verified_at,
    :provenance_verification_method, :provenance_notes
)
"""


def county_params(county: County) -> dict[str, Any]:
    """Return INSERT parameters for a County."""
    return {
        "code": county.code,
        "name": county.name,
        "capital": county.capital,
        "region": county.region,
        **_provenance_params(county.provenance),
    }


def county_from_row(row: Row) -> County:
    """Reconstruct a County from a database row."""
    return County(
        code=row["code"],
        name=row["name"],
        capital=row["capital"],
        region=row["region"],
        provenance=_provenance_from_row(row),
    )


# --- emergency_contacts -----------------------------------------------------

INSERT_EMERGENCY_CONTACT = """
INSERT INTO emergency_contacts (
    county_code, category, name, phone_numbers_json, notes,
    provenance_source, provenance_source_url, provenance_last_verified_at,
    provenance_verification_method, provenance_notes
) VALUES (
    :county_code, :category, :name, :phone_numbers_json, :notes,
    :provenance_source, :provenance_source_url, :provenance_last_verified_at,
    :provenance_verification_method, :provenance_notes
)
"""


def emergency_contact_params(contact: EmergencyContact) -> dict[str, Any]:
    """Return INSERT parameters for an EmergencyContact."""
    return {
        "county_code": contact.county_code,
        "category": contact.category.value,
        "name": contact.name,
        "phone_numbers_json": json.dumps(contact.phone_numbers),
        "notes": contact.notes,
        **_provenance_params(contact.provenance),
    }


def emergency_contact_from_row(row: Row) -> EmergencyContact:
    """Reconstruct an EmergencyContact from a database row."""
    return EmergencyContact(
        county_code=row["county_code"],
        category=row["category"],
        name=row["name"],
        phone_numbers=json.loads(row["phone_numbers_json"]),
        notes=row["notes"],
        provenance=_provenance_from_row(row),
    )


# --- national_numbers -------------------------------------------------------

INSERT_NATIONAL_NUMBER = """
INSERT INTO national_numbers (
    service_name, short_code, alternate_numbers_json, category, description,
    provenance_source, provenance_source_url, provenance_last_verified_at,
    provenance_verification_method, provenance_notes
) VALUES (
    :service_name, :short_code, :alternate_numbers_json, :category, :description,
    :provenance_source, :provenance_source_url, :provenance_last_verified_at,
    :provenance_verification_method, :provenance_notes
)
"""


def national_number_params(number: NationalNumber) -> dict[str, Any]:
    """Return INSERT parameters for a NationalNumber."""
    return {
        "service_name": number.service_name,
        "short_code": number.short_code,
        "alternate_numbers_json": json.dumps(number.alternate_numbers),
        "category": number.category.value,
        "description": number.description,
        **_provenance_params(number.provenance),
    }


def national_number_from_row(row: Row) -> NationalNumber:
    """Reconstruct a NationalNumber from a database row."""
    return NationalNumber(
        service_name=row["service_name"],
        short_code=row["short_code"],
        alternate_numbers=json.loads(row["alternate_numbers_json"]),
        category=row["category"],
        description=row["description"],
        provenance=_provenance_from_row(row),
    )


# --- poison_controls --------------------------------------------------------

INSERT_POISON_CONTROL = """
INSERT INTO poison_controls (
    name, phone_numbers_json, short_codes_json, address, hours, scope, region,
    provenance_source, provenance_source_url, provenance_last_verified_at,
    provenance_verification_method, provenance_notes
) VALUES (
    :name, :phone_numbers_json, :short_codes_json, :address, :hours, :scope, :region,
    :provenance_source, :provenance_source_url, :provenance_last_verified_at,
    :provenance_verification_method, :provenance_notes
)
"""


def poison_control_params(centre: PoisonControl) -> dict[str, Any]:
    """Return INSERT parameters for a PoisonControl."""
    return {
        "name": centre.name,
        "phone_numbers_json": json.dumps(centre.phone_numbers),
        "short_codes_json": json.dumps(centre.short_codes),
        "address": centre.address,
        "hours": centre.hours,
        "scope": centre.scope,
        "region": centre.region,
        **_provenance_params(centre.provenance),
    }


def poison_control_from_row(row: Row) -> PoisonControl:
    """Reconstruct a PoisonControl from a database row."""
    return PoisonControl(
        name=row["name"],
        phone_numbers=json.loads(row["phone_numbers_json"]),
        short_codes=json.loads(row["short_codes_json"]),
        address=row["address"],
        hours=row["hours"],
        scope=row["scope"],
        region=row["region"],
        provenance=_provenance_from_row(row),
    )
