"""Provenance: the audit trail attached to every record in the system.

No domain record exists without a :class:`Provenance`. It records where a piece
of data came from, how it was verified, and when that verification last happened.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, HttpUrl


class VerificationMethod(StrEnum):
    """How a record's accuracy was last confirmed."""

    MANUAL_CALL = "manual_call"
    WEBSITE_CHECK = "website_check"
    OFFICIAL_PUBLICATION = "official_publication"
    MACHINE_IMPORTED = "machine_imported"


class Provenance(BaseModel):
    """Audit metadata describing the origin and verification of a record.

    Attributes:
        source: Human-readable name of the data source.
        source_url: Canonical URL for the source, when one exists.
        last_verified_at: Date the record was last verified.
        verification_method: How the record was verified.
        notes: Optional free-form context about the verification.
    """

    source: str
    source_url: HttpUrl | None = None
    last_verified_at: date
    verification_method: VerificationMethod
    notes: str | None = None
