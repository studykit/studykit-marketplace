# a4 — bootstrap wiki authoring

`a4/bootstrap.md` is the **single source of truth for Launch & Verify**. It records the environment setup, the build/launch commands, and the verified smoke test that proves the workspace "runs". The `## Verify` section in particular is the executable verification contract — never duplicated into other wiki pages.

Frontmatter contract: see `./frontmatter-wiki.md`. Body conventions: see `./wiki-body.md` (`## Change Logs`, Wiki Update Protocol).

## Body shape

**Required:**

- `## Environment` — the runtime environment the workspace requires: language version, package manager, OS-specific notes, env vars needed at runtime. Discovered and recorded — not speculated.
- `## Launch` — the build / start commands, in order. Each command is the **literal** invocation that was verified to work, not a template. Distinguish dev / build / production where applicable.
- `## Verify` — **the executable verification contract.** Contains:
  - Verified test commands (unit, integration, e2e — whichever the project has).
  - The smoke scenario — what running the application from scratch should produce.
  - Test isolation flags — env vars, fixtures, or process flags needed to keep tests deterministic.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was re-derived (dated bullets with markdown links to the causing review item or architecture spec). Most edits to this page are full re-runs, so `## Change Logs` is sparse — record why a re-run was needed. Format and discipline: `./wiki-body.md`.

Unknown H2 headings are tolerated.

### Why `## Verify` lives only here

`## Verify` is the single executable contract that drives implementation verification. Duplicating it into `architecture.md` (test strategy section) would create drift. Architecture's `## Test Strategy` describes the **strategy** (unit / integration / e2e split, isolation philosophy); bootstrap's `## Verify` records the **executable contract** (the actual commands). The two are complementary.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Bootstrap typically links back to `architecture.md` for context on why certain commands or env vars are required.

## Change Log triggers

Most bullets that land on this page cite a `target: architecture` review item that triggered a re-run.

## Common mistakes (bootstrap-specific)

- **Required section missing** (`## Environment`, `## Launch`, `## Verify`).

## Don't

- **Don't write commands that have not been verified.** Bootstrap records what *succeeded*; speculative commands belong in a spec or research artifact, not here.
- **Don't duplicate `## Verify` content into `architecture.md`.** It references, it does not duplicate.
- **Don't write architecture rationale here.** The why behind the stack lives in `architecture.md` and the spec(s) that shaped it. Bootstrap records the *how to run it*.
- **Don't write task-level information here.** Per-task verification belongs in the task's `## Unit Test Strategy` section.
- **Don't append `## Change Logs` bullets without a markdown link.**
- **Don't manually archive the prior copy.** Archive on re-run is automated; manual moves break the audit trail.
