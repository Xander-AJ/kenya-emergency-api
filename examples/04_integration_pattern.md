# Integration pattern: composing with `rag-guardrails-starter`

This is a design sketch, not shipped code. It shows how `kenya-emergency`
is meant to slot into [`rag-guardrails-starter`](https://github.com/Xander-AJ/rag-guardrails-starter)
once a small integration seam exists in that project — and why these are
**two civic-tech packages that compose, not one project artificially split in
two.**

## The story

`rag-guardrails-starter` has an emergency-detection layer: when a user message
looks like a real-world emergency ("someone collapsed, what do I call?"), the
guardrail short-circuits the model and surfaces real emergency contacts instead
of letting an LLM improvise them. Today that layer hardcodes Kenyan emergency
numbers as constants.

Hardcoded constants are the right call for a *starter* — zero dependencies, easy
to read. But they go stale, they're Nairobi-by-assumption, and they carry no
provenance. `kenya-emergency` is the opposite trade: a verified, versioned,
provenance-bearing data layer. The two fit together through a narrow interface
so neither has to absorb the other.

## The seam: an `EmergencyContactProvider` Protocol

The integration point is a structural `Protocol` that `rag-guardrails-starter`
would define for its own needs. It depends on *the shape*, not on
`kenya-emergency` — so the starter keeps working with its hardcoded defaults and
takes a richer provider only if one is supplied.

```python
# Lives in rag-guardrails-starter (sketch — not implemented there yet).
from typing import Protocol, runtime_checkable


@runtime_checkable
class EmergencyContactProvider(Protocol):
    """What the guardrail needs from any emergency-data source."""

    def police_emergency(self) -> object | None: ...
    def ambulance_emergency(self) -> object | None: ...
    def emergency_overview(self, code_or_name: str) -> object: ...
```

`EmergencyService` already satisfies this shape — no adapter, no subclassing, no
import of the starter. Structural typing means the seam stays one-directional:
the starter declares what it wants; `kenya-emergency` happens to provide it.

## How `kenya-emergency` slots in

```python
# In rag-guardrails-starter, once the seam exists:
from kenya_emergency import EmergencyService

# The guardrail accepts any EmergencyContactProvider; default stays hardcoded.
guardrail = EmergencyGuardrail(contact_provider=EmergencyService())

# When the detector fires on a Kenyan-locale conversation, the guardrail can now
# answer with verified, provenance-bearing data instead of baked-in constants:
overview = guardrail.contact_provider.emergency_overview("Nairobi")
```

The starter degrades gracefully: with no provider passed, it uses its constants;
with `EmergencyService` passed, it uses verified data. Nothing about the
guardrail's control flow changes.

## Why two packages, not one

- **Different release cadences.** Emergency *data* gets re-verified on a fixed
  schedule (see [`DATA_PROVENANCE.md`](../DATA_PROVENANCE.md)); guardrail *logic*
  changes when models and threats change. Coupling them would force one to
  re-release on the other's clock.
- **Different audiences.** Someone building a community SMS bot wants the data
  and never touches a RAG pipeline. Someone hardening an LLM app wants the
  guardrail and may bring their own data. Each package has a clean, standalone
  story.
- **A narrow, honest interface.** A `Protocol` with three methods is a contract
  small enough to keep stable. The dependency points one way (starter → data
  shape), so there is no release-coupling and no circular import.

Two packages that compose by design beats one package that does two jobs and
couples their failure modes.
