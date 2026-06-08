#!/usr/bin/env python3
"""Direct EmergencyService usage — the Python-package surface.

This script exercises the whole read API in one self-narrating run: each section
prints a ``# ...`` header so the output reads top-to-bottom like a transcript.

Running against fixtures
------------------------
Until v1.0 ships verified data, the package's bundled ``data/snapshots/``
directory is empty. So this example points the service at the small, real-shape
test fixtures via ``KENYA_EMERGENCY_SNAPSHOT_DIR``. When v1.0 lands, the bundled
snapshots will be populated and ``EmergencyService()`` will work with no env vars
at all — drop the two ``os.environ`` lines and the script is unchanged.

We also redirect ``KENYA_EMERGENCY_DB_PATH`` to a temp file so the lazily-built
SQLite database never pollutes the source tree.

    python examples/01_python_client.py
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# --- point the service at fixtures BEFORE importing the package -------------
# Settings reads these env vars (prefix KENYA_EMERGENCY_) at construction time.
_FIXTURES = Path(__file__).resolve().parent.parent / "tests" / "data" / "snapshots"
_DB_FILE = Path(tempfile.gettempdir()) / "kea_example_01.db"
os.environ["KENYA_EMERGENCY_SNAPSHOT_DIR"] = str(_FIXTURES)
os.environ["KENYA_EMERGENCY_DB_PATH"] = str(_DB_FILE)

from kenya_emergency import ContactCategory, EmergencyService  # noqa: E402
from kenya_emergency.core.exceptions import DataNotFoundError  # noqa: E402


def main() -> None:
    print("# Construct EmergencyService() with default Settings")
    # No arguments: Settings() is read from the environment/defaults, and the
    # SQLite database is auto-built from the snapshot dir on first use.
    service = EmergencyService()
    meta = service.metadata()
    counties_loaded = meta.record_counts.get("counties", 0)
    print(f"  dataset built at {meta.built_at}, {counties_loaded} counties loaded\n")

    print("# List counties (ordered by code)")
    for county in service.counties():
        print(f"  {county.code}  {county.name}  (capital: {county.capital})")
    print()

    print("# Look up a county by code — normalized: '47' -> '047'")
    nairobi = service.county("47")
    print(f"  '47' resolved to {nairobi.code} {nairobi.name}\n")

    print("# Emergency contacts for Nairobi, filtered to FIRE")
    fire = service.contacts_for_county("047", category=ContactCategory.FIRE)
    for contact in fire:
        print(f"  {contact.category.value}: {contact.name} -> {contact.phone_numbers}")
    print()

    print("# National emergency numbers: police and ambulance")
    police = service.police_emergency()
    ambulance = service.ambulance_emergency()
    if police is not None:
        print(f"  police: {police.service_name} dial {police.short_code}")
    else:
        print("  police: (no entry in this dataset)")
    if ambulance is not None:
        print(f"  ambulance: {ambulance.service_name} dial {ambulance.short_code}")
    else:
        print("  ambulance: (no entry in fixtures — added with verified data in v1.0)")
    print()

    print("# Composite use case: emergency_overview('Nairobi')")
    overview = service.emergency_overview("Nairobi")
    print(f"  county: {overview.county.name}")
    print(f"  contact categories present: {[c.value for c in overview.contacts_by_category]}")
    print(f"  national numbers: {[n.short_code for n in overview.national_numbers]}")
    print(f"  national poison control centres: {len(overview.poison_controls)}\n")

    print("# Error handling: DataNotFoundError on a well-formed but absent code")
    try:
        service.county("046")  # valid shape, no such county in the dataset
    except DataNotFoundError as exc:
        print(f"  caught DataNotFoundError: {exc}\n")

    print("# Error handling: ValueError on malformed input")
    try:
        service.county("abc")  # not a county-code shape at all
    except ValueError as exc:
        print(f"  caught ValueError: {exc}")


if __name__ == "__main__":
    main()
