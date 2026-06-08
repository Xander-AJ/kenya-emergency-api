"""Poison control model.

A poison information / control centre, either national or regional in scope.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from kenya_emergency.models.phone import KenyanPhoneNumber
from kenya_emergency.models.provenance import Provenance


class PoisonControl(BaseModel):
    """A poison information / control centre.

    v1 scope: a centre carries at least one full phone number plus optional short
    dialer codes. ``scope`` distinguishes national centres from regional ones;
    regional centres must name their ``region``.

    Attributes:
        name: Centre name (e.g., "KEMRI Poisons Information Centre").
        phone_numbers: One or more numbers, normalized to E.164.
        short_codes: Optional 3-5 digit dialer codes.
        address: Optional physical address.
        hours: Optional free-form operating hours (e.g., "24/7").
        scope: Whether the centre serves the whole nation or a region.
        region: Region served; required when ``scope == "regional"``.
        provenance: Required audit trail for this record.
    """

    name: str
    phone_numbers: list[KenyanPhoneNumber] = Field(min_length=1)
    short_codes: list[Annotated[str, Field(pattern=r"^\d{3,5}$")]] = Field(default_factory=list)
    address: str | None = None
    hours: str | None = None
    scope: Literal["national", "regional"]
    region: str | None = None
    provenance: Provenance

    @model_validator(mode="after")
    def _validate_region_for_scope(self) -> PoisonControl:
        """A regional centre must specify which region it serves."""
        if self.scope == "regional" and self.region is None:
            raise ValueError("region is required when scope == 'regional'")
        return self
