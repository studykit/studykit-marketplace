# Codebase Assessment

Two orthogonal axes determine the work scope — both must be resolved.

## Axis 1 — project state (fresh vs incremental)

- **No existing code** → fresh bootstrap. Run all subsequent steps from scratch.
- **Existing code** → incremental. Identify what's already present (project structure, dependencies, build config, test setup). Only set up what's missing. Do not overwrite existing working configuration without cause.

## Axis 2 — pipeline shape (Full vs Minimal)

See `../../../dev/pipeline-shapes.md` for shape definitions.

- **Full shape** (`architecture.md` is the input) — extract Technology Stack, Component structure, Test Strategy, External Dependencies from `architecture.md` and execute against that. Canonical case.
- **Minimal shape** (`architecture.md` may be absent) — when invoked directly without architecture authoring (e.g., a brownfield single-change project entering through `/a4:task` or `/a4:bug`), derive build / launch / test commands from the observed project state plus minimal user input. Produce a `bootstrap.md` that captures the verified L&V commands; do not back-fill an `architecture.md`. The bootstrap wiki page itself is the only required anchor in Minimal shape.

## Axis combinations

- Greenfield + Full → canonical greenfield bootstrap.
- Brownfield + Full → incremental case after `/a4:arch` has run.
- Brownfield + Minimal → single-change case where `architecture.md` does not exist.
