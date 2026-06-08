"""County model.

Represents one of Kenya's 47 counties as defined by the 2010 Constitution,
keyed by its official two-digit county code (zero-padded to three characters,
"001" through "047").
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from kenya_emergency.models.provenance import Provenance


def _validate_county_code_range(value: str) -> str:
    """Reject syntactically valid codes that fall outside the 001-047 range."""
    if not 1 <= int(value) <= 47:
        raise ValueError(f"county code {value!r} is outside the valid range 001-047")
    return value


#: A Kenyan county code: three digits, "001" through "047". Reusable across any
#: model that references a county.
CountyCode = Annotated[
    str,
    Field(pattern=r"^0[0-4][0-9]$"),
    AfterValidator(_validate_county_code_range),
]


class County(BaseModel):
    """A Kenyan county and its administrative metadata.

    v1 scope: the constitutionally defined 47 counties. ``region`` is a free-form
    grouping string (no controlled vocabulary yet) and is optional.

    Attributes:
        code: Official county code, "001"-"047".
        name: County name (e.g., "Nairobi").
        capital: County headquarters / capital (e.g., "Nairobi City").
        region: Optional broader regional grouping (e.g., "Coast", "Nyanza").
        provenance: Required audit trail for this record.
    """

    code: CountyCode
    name: str
    capital: str
    region: str | None = None
    provenance: Provenance
