"""SQLite schema for kenya-emergency-api.

The schema is intentionally denormalized and storage-only: list-valued fields
(phone numbers, short codes) are kept as JSON-encoded ``TEXT`` columns, and every
domain table carries five ``provenance_*`` columns flattened from the embedded
:class:`~kenya_emergency.models.provenance.Provenance` record.

Conventions:
    * Required fields use ``TEXT NOT NULL``; nullable fields use ``TEXT``.
    * Dates and datetimes are stored as ISO 8601 strings.
    * URLs are stored as strings (``None`` becomes SQL ``NULL``).
    * Enums are stored as their string value.
"""

from __future__ import annotations

#: Full DDL for the database. Safe to run repeatedly (``IF NOT EXISTS``).
SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS counties (
    code                            TEXT NOT NULL PRIMARY KEY,
    name                            TEXT NOT NULL,
    capital                         TEXT NOT NULL,
    region                          TEXT,
    provenance_source               TEXT NOT NULL,
    provenance_source_url           TEXT,
    provenance_last_verified_at     TEXT NOT NULL,
    provenance_verification_method  TEXT NOT NULL,
    provenance_notes                TEXT
);

CREATE TABLE IF NOT EXISTS emergency_contacts (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    county_code                     TEXT NOT NULL REFERENCES counties(code),
    category                        TEXT NOT NULL,
    name                            TEXT NOT NULL,
    phone_numbers_json              TEXT NOT NULL,
    notes                           TEXT,
    provenance_source               TEXT NOT NULL,
    provenance_source_url           TEXT,
    provenance_last_verified_at     TEXT NOT NULL,
    provenance_verification_method  TEXT NOT NULL,
    provenance_notes                TEXT
);

CREATE INDEX IF NOT EXISTS idx_emergency_contacts_county_category
    ON emergency_contacts (county_code, category);

CREATE TABLE IF NOT EXISTS national_numbers (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    service_name                    TEXT NOT NULL,
    short_code                      TEXT NOT NULL,
    alternate_numbers_json          TEXT NOT NULL,
    category                        TEXT NOT NULL,
    description                     TEXT NOT NULL,
    provenance_source               TEXT NOT NULL,
    provenance_source_url           TEXT,
    provenance_last_verified_at     TEXT NOT NULL,
    provenance_verification_method  TEXT NOT NULL,
    provenance_notes                TEXT
);

CREATE TABLE IF NOT EXISTS poison_controls (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    name                            TEXT NOT NULL,
    phone_numbers_json              TEXT NOT NULL,
    short_codes_json                TEXT NOT NULL,
    address                         TEXT,
    hours                           TEXT,
    scope                           TEXT NOT NULL,
    region                          TEXT,
    provenance_source               TEXT NOT NULL,
    provenance_source_url           TEXT,
    provenance_last_verified_at     TEXT NOT NULL,
    provenance_verification_method  TEXT NOT NULL,
    provenance_notes                TEXT
);

CREATE TABLE IF NOT EXISTS _metadata (
    key     TEXT NOT NULL PRIMARY KEY,
    value   TEXT NOT NULL
);
"""
