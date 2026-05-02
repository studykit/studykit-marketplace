# Test-Tier Assessment

Decide which test tiers this project needs and which are already present.

## Sources

- `architecture.md` Test Strategy section — when present, treat as canonical input. It lists which tiers (unit / integration / E2E) the project commits to and any host-specific notes.
- Existing config files — `package.json` scripts, `pytest.ini`, `vitest.config.*`, `wdio.conf.*`, `.github/workflows/*` — confirm what is already wired.
- Project type defaults — when `architecture.md` is absent:
  - **Library / pure-logic project** — unit only by default.
  - **Application with external boundaries (API, CLI talking to services, GUI)** — unit + integration.
  - **End-user application that exercises a UI** — unit + integration + E2E (E2E only when the UI surface is stable enough to test against).

## Output of this step

A short list of `(tier, status)` pairs:

- `unit` — `present` / `missing`
- `integration` — `present` / `missing` / `not-needed`
- `E2E` — `present` / `missing` / `not-needed`

The next step (`./test-infrastructure.md`) acts on the `missing` entries; `present` entries are left untouched unless the test strategy explicitly changed.
