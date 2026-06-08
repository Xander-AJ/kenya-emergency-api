"""Integration test: snapshot -> builder -> adapter round-trip."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from kenya_emergency.models.county import County
from kenya_emergency.models.emergency_contact import ContactCategory
from kenya_emergency.models.provenance import Provenance, VerificationMethod
from kenya_emergency.storage import SQLiteAdapter


def test_county_round_trips_with_full_fidelity(built_db: Path) -> None:
    """A County read back equals the snapshot record, provenance included."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    expected = County(
        code="047",
        name="Nairobi",
        capital="Nairobi City",
        region="Nairobi Metropolitan",
        provenance=Provenance(
            source="Kenya Gazette",
            source_url="https://www.ndoc.go.ke/",  # type: ignore[arg-type]
            last_verified_at=date(2026, 1, 10),
            verification_method=VerificationMethod.OFFICIAL_PUBLICATION,
            notes=None,
        ),
    )

    assert adapter.get_county("047") == expected


def test_phone_numbers_round_trip_normalized(built_db: Path) -> None:
    """A local-format snapshot number comes back as canonical E.164."""
    adapter = SQLiteAdapter(built_db, auto_build=False)

    contacts = adapter.get_emergency_contacts("047", category=ContactCategory.POLICE)

    assert len(contacts) == 1
    assert contacts[0].phone_numbers == ["+254712345678"]
