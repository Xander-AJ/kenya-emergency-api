# kenya-emergency-api

> Civic-tech infrastructure for Kenyan emergency contacts, national emergency numbers, and poison control. A Python package and a self-hostable HTTP API, sharing a single verified data layer.

When someone in Kenya needs help, the developers building the apps they reach for shouldn't be hardcoding emergency numbers from memory. This is that data layer — vendored, verified, versioned, and free to use.

**Status:** v1 in development. The codebase is complete; the verified data is currently being curated against official sources. Until v1.0 ships, the package contains structure and fixtures but no production emergency contacts.

## What you get

- 47 Kenyan counties with codes, capitals, and regional metadata
- Per-county emergency contacts: police, fire, ambulance, Red Cross, GBV helpline, child helpline
- National emergency numbers (999, 911, 112, 1199, 1195, 116)
- Poison control centers
- Every record carries explicit provenance — source, verification method, last-verified date
- Phone numbers normalized to E.164 via libphonenumber

Hospital and facility data is **not** included in v1. That's planned for v1.1, where it will be added with the same provenance discipline rather than dumped in raw from KMHFL exports.

## Two ways to use it

### As a Python package

```python
from kenya_emergency import EmergencyService, ContactCategory

service = EmergencyService()  # auto-builds local SQLite from bundled snapshots

# Look up a county (accepts "47" or "047")
nairobi = service.county("47")

# Get fire brigade contacts for that county
fire = service.contacts_for_county("047", category=ContactCategory.FIRE)

# Composite use case: everything for one place
overview = service.emergency_overview("Nairobi")
```

### As an HTTP API (self-host)

```bash
pip install kenya-emergency
uvicorn kenya_emergency.api.app:app --port 8000
```

```bash
curl http://localhost:8000/v1/counties/047
curl http://localhost:8000/v1/counties/047/contacts?category=ambulance
curl http://localhost:8000/v1/emergency/overview/Nairobi
```

Full OpenAPI docs at `/docs` once the server's running.

## Why provenance is a first-class concept

Every record in this system answers four questions: where did this come from, who verified it, when was it last verified, and how. No record exists without that audit trail. It's not garnish — it's the difference between data a developer can responsibly route a user toward and data they can't.

See [DATA_PROVENANCE.md](./DATA_PROVENANCE.md) for the full verification policy and re-verification cadence.

## What this is not

- Not a replacement for calling 999, 911, or 112 in an actual emergency
- Not a real-time service — data is vendored snapshots refreshed on a schedule, not live feeds
- Not a hospital directory yet (coming in v1.1, verified per-facility via web sources)
- Not affiliated with the Government of Kenya, Kenya Red Cross, or any official body
- Not a substitute for due diligence in any application that touches medical or safety decisions

The MIT license disclaims warranty. The provenance discipline tries to earn trust anyway.

## Install

```bash
pip install kenya-emergency
```

For the optional Supabase storage adapter (v1.1):

```bash
pip install "kenya-emergency[supabase]"
```

## Project shape

A single core service layer with two surfaces — a Python import and a FastAPI server — and a swappable storage adapter (SQLite default, Supabase planned). Read [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for the full architecture.

## Companion project

This package was originally born out of the emergency-detection layer in [rag-guardrails-starter](https://github.com/Xander-AJ/rag-guardrails-starter), which hardcodes Kenyan emergency numbers as constants. This is the public-infrastructure version of that same thinking: the data anyone building an AI or community app for Kenya can reach for instead of starting from scratch.

The two projects compose well by design but stay independent — fewer release-coupling problems, cleaner story for each.

## Contributing

Verified data is the work that matters. Contributing a single accurate county record is more valuable than another code feature. See [CONTRIBUTING.md](./CONTRIBUTING.md) — particularly the verification checklist.

## License

MIT. See [LICENSE](./LICENSE).

---

Built in Nairobi by [Norah Labs](https://github.com/Xander-AJ).
