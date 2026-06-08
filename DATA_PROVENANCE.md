# Data Provenance

## Why provenance matters

This is emergency data. If a phone number here is wrong or stale, someone trying
to reach the police, an ambulance, or a poison-control centre during a real
crisis reaches a dead line instead — staleness has a human cost, measured in
minutes that matter. That is why every record in this dataset carries an explicit
audit trail: where it came from, how it was checked, and when it was last
checked. A record without provenance is not data we will ship, because it is not
data a developer can responsibly route a person toward. Provenance is not
metadata garnish; it is the contract that makes this dataset usable for the
purpose it exists for.

## Verification methods explained

Every record's provenance includes a `verification_method`, one of four values
(the `VerificationMethod` enum). Choose the strongest method available for the
record:

| Method | Value | When it applies |
| --- | --- | --- |
| Manual call | `manual_call` | A human dialed the number and confirmed it reaches the stated service. The strongest evidence for a contact number — preferred for county-level emergency contacts and poison-control lines. |
| Official publication | `official_publication` | The record is taken from an authoritative published source (Kenya Gazette, a government directory, an official agency notice). Best for stable facts like county codes and nationally mandated short codes (999, 112). |
| Website check | `website_check` | The value was read from the official website of the responsible body (a county government, the Kenya Red Cross). Use when a published document or a manual call isn't available, and record the exact URL. |
| Machine imported | `machine_imported` | The record was bulk-imported from a dataset and has **not** yet been independently verified by a human. This is the weakest level — treat such records as provisional and prioritize them for re-verification. |

## Snapshot file inventory

The dataset ships as versioned JSON snapshots in `data/snapshots/`. Each file is
an array of records; every record carries a required `provenance` object
(`source`, `source_url`, `last_verified_at`, `verification_method`, `notes`).
Phone numbers are normalized to E.164 on load.

### `counties_v1.json`

The 47 constitutionally defined counties.

| Field | Expectation |
| --- | --- |
| `code` | County code, `"001"`–`"047"` (three digits, zero-padded). |
| `name` | County name, e.g. `"Nairobi"`. |
| `capital` | County headquarters / capital town. |
| `region` | Optional broader grouping, e.g. `"Coast"` (free-form, may be null). |
| `provenance` | Required. Typically `official_publication` (Kenya Gazette). |

### `emergency_contacts_v1.json`

County-scoped emergency services with full dialable numbers.

| Field | Expectation |
| --- | --- |
| `county_code` | The county served, `"001"`–`"047"`. Must match a county. |
| `category` | One of: `police`, `fire`, `ambulance`, `redcross`, `gbv`, `child_helpline`, `general`. |
| `name` | Service name, e.g. `"Nairobi County Fire Brigade"`. |
| `phone_numbers` | At least one full number; normalized to E.164. No short codes here. |
| `notes` | Optional free-form context (e.g. `"Operations desk"`). |
| `provenance` | Required. Prefer `manual_call` for contact numbers. |

### `national_emergency_numbers_v1.json`

Nationwide services reachable by a short dialer code.

| Field | Expectation |
| --- | --- |
| `service_name` | Service name, e.g. `"Police Emergency"`. |
| `short_code` | 3–5 digit dialer code (`"999"`, `"112"`, `"1199"`) — a code, not a phone number. |
| `alternate_numbers` | Optional full-format alternate lines, normalized to E.164. |
| `category` | Same category vocabulary as emergency contacts. |
| `description` | Human-readable description of the service. |
| `provenance` | Required. Prefer `official_publication` for mandated codes. |

### `poison_control_v1.json`

Poison information / control centres.

| Field | Expectation |
| --- | --- |
| `name` | Centre name, e.g. `"KEMRI Poisons Information Centre"`. |
| `phone_numbers` | At least one full number; normalized to E.164. |
| `short_codes` | Optional 3–5 digit dialer codes. |
| `address` | Optional physical address. |
| `hours` | Optional operating hours, e.g. `"24/7"`. |
| `scope` | `"national"` or `"regional"`. |
| `region` | Required when `scope == "regional"`; otherwise null. |
| `provenance` | Required. Prefer `manual_call`. |

## Re-verification cadence (policy)

Emergency data decays. The following re-verification schedule is **policy**, not
a suggestion — a record whose `last_verified_at` is older than its cadence is
considered stale and must be re-verified before the next release:

| Data category | Re-verify every |
| --- | --- |
| National emergency numbers | 12 months |
| Per-county emergency contacts | 6 months |
| Poison control centres | 12 months |

County administrative facts (codes, names, capitals) change only with
constitutional/legal amendment and are re-verified opportunistically rather than
on a fixed clock.

## Verification checklist for new records

Before a record is added or updated, the contributor confirms:

- [ ] The number was reached or confirmed via the strongest method available
      (a `manual_call` beats a `website_check` beats an unverified import).
- [ ] `verification_method` honestly reflects what was actually done — never
      claim `manual_call` for a number that was only read off a page.
- [ ] `source` names the specific responsible body, not a generic aggregator.
- [ ] `source_url` points to the canonical page for that source where one exists.
- [ ] `last_verified_at` is the date the check was *actually performed*.
- [ ] Phone numbers are real, in service, and reach the stated service (not a
      switchboard that has since changed).
- [ ] `category` / `scope` are correct, and `county_code` (where present) maps to
      a real county.
- [ ] Anything uncertain is captured in `notes` rather than silently dropped.

## Source registry

Filled in as snapshots are curated. One row per source contribution.

| Source | URL | Last accessed | Data category | Records contributed |
| --- | --- | --- | --- | --- |
| Constitution of Kenya 2010, First Schedule | http://kenyalaw.org/lex/actview.xql?actid=Const2010 | 2026-06-08 | Counties | 47 |
| National Police Service | https://www.nationalpolice.go.ke | 2026-06-08 | National emergency numbers | 1 |
| OSAC Kenya Country Security Report | https://www.osac.gov | 2026-06-08 | National emergency numbers | 3 |
| Kenya Red Cross Society | https://www.redcross.or.ke | 2026-06-08 | National emergency numbers | 1 |
| Healthcare Assistance Kenya (HAK) | https://hakgbv1195.org | 2026-06-08 | National emergency numbers | 1 |
| Childline Kenya / Dept of Children Services | https://childlinekenya.co.ke | 2026-06-08 | National emergency numbers | 1 |
| Pharmacy and Poisons Board | https://web.pharmacyboardkenya.org/contacts/ | 2026-06-08 | Poison control | 1 |

## Known limitations & gaps

- Kenya lacks a dedicated 24/7 poison control hotline. The PPB entry is included
  as the regulatory authority but is not an emergency service. For poisoning
  emergencies, general emergency numbers (999, 112) and the Kenya Red Cross
  (1199) are the appropriate contacts.
- Per-county emergency contacts are not yet curated. The
  `emergency_contacts_v1.json` file is intentionally empty and will be populated
  county-by-county with verified data in a follow-up release.
