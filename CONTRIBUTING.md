# Contributing

Thanks for helping build civic-tech infrastructure people can rely on. This
project holds itself to a simple bar: **production-grade code, not demo code.**
That applies to a one-line fix as much as to a new feature.

## Local setup

```bash
# 1. Clone
git clone https://github.com/Xander-AJ/kenya-emergency-api.git
cd kenya-emergency-api

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install the package with dev dependencies (editable)
pip install -e ".[dev]"

# 4. Run the tests
pytest
```

If you'll touch the Supabase adapter, also install its extra:
`pip install -e ".[dev,supabase]"`.

## Code style

`ruff` and `mypy` must both be clean before a PR is opened — CI enforces this,
so save yourself a round-trip and run them locally:

```bash
ruff check .          # lint
ruff format --check . # formatting (run `ruff format .` to fix)
mypy src/             # strict type checking
```

## Commit conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — a new capability
- `fix:` — a bug fix
- `chore:` — tooling, deps, scaffolding
- `docs:` — documentation only
- `test:` — tests only

Scope is encouraged, e.g. `feat(services): ...`, `fix(api): ...`.

**No co-author trailers.** Do not add `Co-authored-by:` (or similar) trailers to
commits — this matches the project's existing history. Keep commit messages
about the change, not the tooling that produced it.

## Contributing data

Verified data is the work that matters most here — a single accurate county
record is worth more than another code feature.

- Read [DATA_PROVENANCE.md](./DATA_PROVENANCE.md) first. It is the contract.
- **Every record needs provenance.** No record is merged without a complete
  `provenance` block (source, source URL, last-verified date, verification
  method). A record you can't attribute is a record we can't ship.
- Follow the
  [verification checklist for new records](./DATA_PROVENANCE.md#verification-checklist-for-new-records)
  before submitting. Be honest about `verification_method` — never claim a
  `manual_call` you didn't make.
- Respect the
  [re-verification cadence](./DATA_PROVENANCE.md#re-verification-cadence-policy):
  county contacts every 6 months, national numbers and poison control every 12.

## Contributing code

- **Small, focused PRs.** One concern per PR; it reviews faster and reverts
  cleanly.
- **Full type hints.** The codebase is `mypy --strict`; new code matches it.
- **Tests required.** New behavior comes with tests; bug fixes come with a test
  that fails before the fix and passes after.
- **Docstrings on public APIs.** Anything a consumer imports or calls gets a
  docstring explaining what it does, its arguments, and what it raises.
- Match the style of the surrounding code rather than introducing a new one.

## The bar

Production-grade code, not demo code. If you wouldn't want it routing a real
person to real help during a real emergency, it isn't ready to merge.
