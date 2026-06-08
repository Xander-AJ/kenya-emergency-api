# Project Structure

## Repository layout

```
kenya-emergency-api/
├── pyproject.toml                  # Build (hatchling), deps, ruff/mypy/pytest config
├── README.md                       # Project overview and quickstart
├── CONTRIBUTING.md                 # Setup, code style, commit + data conventions
├── DATA_PROVENANCE.md              # Provenance policy, verification cadence, registry
├── PROJECT_STRUCTURE.md            # This document
├── LICENSE                         # MIT
├── .env.example                    # Sample environment configuration
│
├── data/
│   └── snapshots/                  # Vendored JSON snapshots shipped in the wheel
│       └── .gitkeep                #   (empty until v1.0 data curation lands)
│
├── scripts/
│   └── build_db.py                 # CLI to build the SQLite DB from snapshots
│
├── examples/
│   ├── README.md                   # Index of the examples
│   ├── 01_python_client.py         # Direct EmergencyService usage
│   ├── 02_running_the_api.py       # Programmatic uvicorn server start
│   ├── 03_curl_examples.sh         # HTTP smoke tour (happy + error paths)
│   └── 04_integration_pattern.md   # Protocol seam with rag-guardrails-starter
│
├── src/kenya_emergency/
│   ├── __init__.py                 # Public exports (EmergencyService, models, create_app)
│   ├── version.py                  # __version__
│   ├── client.py                   # Back-compat re-export of EmergencyService
│   │
│   ├── core/
│   │   ├── config.py               # Settings (env-driven, pydantic-settings)
│   │   ├── exceptions.py           # Error hierarchy (DataNotFoundError, StorageError, …)
│   │   └── logging.py              # Logging setup
│   │
│   ├── models/                     # Pydantic domain models (the data contract)
│   │   ├── provenance.py           # Provenance + VerificationMethod (on every record)
│   │   ├── county.py               # County + CountyCode type
│   │   ├── emergency_contact.py    # EmergencyContact + ContactCategory
│   │   ├── national_number.py      # NationalNumber (short dialer codes)
│   │   ├── poison_control.py       # PoisonControl
│   │   ├── phone.py                # KenyanPhoneNumber (E.164 normalization)
│   │   └── overview.py             # EmergencyOverview (composite response)
│   │
│   ├── services/
│   │   ├── emergency_service.py    # EmergencyService — the core read API
│   │   └── _normalize.py           # Forgiving input normalization (code/name/category)
│   │
│   ├── storage/                    # Swappable storage layer
│   │   ├── base.py                 # StorageAdapter ABC + StorageMetadata
│   │   ├── sqlite_adapter.py       # Default adapter (lazy-builds from snapshots)
│   │   ├── supabase_adapter.py     # Optional adapter (v1.1, [supabase] extra)
│   │   ├── builder.py              # Builds SQLite DB from JSON snapshots
│   │   ├── schema.py               # SQLite schema (storage-only, denormalized)
│   │   └── _serde.py               # Row <-> model conversion (single source of truth)
│   │
│   └── api/                        # FastAPI surface (thin wrappers over the service)
│       ├── app.py                  # create_app() factory + module-level app
│       ├── dependencies.py         # get_service() — lazy, cached on app.state
│       ├── middleware.py           # Request-ID correlation middleware
│       ├── error_handlers.py       # Consistent JSON error contract
│       └── routes/                 # counties, emergency, poison, health/metadata
│
└── tests/
    ├── conftest.py                 # Shared fixtures (built_db, sample_provenance)
    ├── data/snapshots/             # Small real-shape JSON fixtures
    ├── unit/                       # Per-module unit tests
    └── integration/               # End-to-end service + API + storage roundtrip
```

## Why this shape

**Two surfaces, one core.** All behavior lives in a single transport-agnostic
service layer — `EmergencyService`. The Python-package surface *is* that class;
the HTTP surface is a thin FastAPI layer whose routes contain no business logic,
only translation between HTTP and service calls (and service exceptions into a
consistent JSON error contract). There is exactly one place where lookups,
normalization, and use-case composition happen, so the import API and the API
server can never disagree about what the data means.

**A swappable storage abstraction.** The service depends on a `StorageAdapter`
interface, not a concrete database. SQLite is the default — zero-config,
file-based, lazily built on first use — and Supabase is a drop-in alternative
(shipped as an optional extra for v1.1). Because every adapter reconstructs rows
*through the Pydantic models*, reads double as schema validation regardless of
backend, and swapping storage changes nothing the service or callers can observe.

**A snapshot pipeline, not a live database.** The source of truth is the set of
versioned JSON snapshots in `data/snapshots/`, each record carrying full
provenance. `builder.py` compiles those snapshots into a SQLite database
atomically (build into a temp file, fsync, rename), and `_serde.py` is the single
module that knows the row↔model mapping in both directions so they cannot drift.
This keeps the data auditable and reviewable as plain text in version control,
makes every release a known, frozen artifact, and means "updating the data" is a
reviewed snapshot change rather than a mutable production database nobody can
diff.
