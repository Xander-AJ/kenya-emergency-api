"""Unit tests for the Provenance model."""

from __future__ import annotations

from datetime import date

from kenya_emergency.models.provenance import Provenance, VerificationMethod


def test_provenance_round_trips_through_json() -> None:
    """A fully-populated Provenance survives a JSON serialize/deserialize cycle."""
    original = Provenance(
        source="Kenya National Disaster Operations Centre",
        source_url="https://www.ndoc.go.ke/",  # type: ignore[arg-type]
        last_verified_at=date(2026, 1, 15),
        verification_method=VerificationMethod.MANUAL_CALL,
        notes="Confirmed by phone with the duty officer.",
    )

    restored = Provenance.model_validate_json(original.model_dump_json())

    assert restored == original


def test_machine_imported_allows_last_verified_today() -> None:
    """A machine-imported record may be verified as of today with no special-casing."""
    today = date.today()

    provenance = Provenance(
        source="Automated snapshot importer",
        last_verified_at=today,
        verification_method=VerificationMethod.MACHINE_IMPORTED,
    )

    assert provenance.verification_method is VerificationMethod.MACHINE_IMPORTED
    assert provenance.last_verified_at == today
