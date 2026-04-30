# a4 — bootstrap wiki authoring

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

`a4/bootstrap.md` is the **single source of truth for Launch & Verify**. It records the environment setup, the build/launch commands, and the verified smoke test that proves the workspace "runs". The `## Verify` section in particular is the executable verification contract — never duplicated into other wiki pages.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`. Wiki pages share a minimal schema (`type:` + `updated:`) — the YAML below is the full contract.

## Frontmatter contract (do not deviate)

```yaml
---
type: bootstrap
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `bootstrap`.
- `updated:` is an unquoted ISO date. Bump on every re-run.
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Environment`, `## Launch`, `## Verify`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Environment` — the runtime environment the workspace requires: language version, package manager, OS-specific notes, env vars needed at runtime. Discovered and recorded — not speculated.
- `## Launch` — the build / start commands, in order. Each command is the **literal** invocation that was verified to work, not a template. Distinguish dev / build / production where applicable.
- `## Verify` — **the executable verification contract.** Contains:
  - Verified test commands (unit, integration, e2e — whichever the project has).
  - The smoke scenario — what running the application from scratch should produce.
  - Test isolation flags — env vars, fixtures, or process flags needed to keep tests deterministic.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was re-derived (dated bullets with markdown links to the causing review item or architecture spec). Most edits to this page are full re-runs, so `## Change Logs` is sparse — record why a re-run was needed.

Unknown H2 headings are tolerated.

### Why `## Verify` lives only here

`## Verify` is the single executable contract that drives implementation verification. Duplicating it into `architecture.md` (test strategy section) or `roadmap.md` would create drift. Architecture's `## Test Strategy` describes the **strategy** (unit / integration / e2e split, isolation philosophy); bootstrap's `## Verify` records the **executable contract** (the actual commands). The two are complementary.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Bootstrap typically links back to `architecture.md` for context on why certain commands or env vars are required.

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — re-run after arch version-incompatibility fix
- YYYY-MM-DD — [spec/<id>-<slug>](spec/<id>-<slug>.md) — added smoke scenario for new component
```

Create the section if absent. Most bullets cite a `target: architecture` review item that triggered the re-run.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Environment`, `## Launch`, `## Verify`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename — the `type:` value must equal the file basename.

## Don't

- **Don't write commands that have not been verified.** Bootstrap records what *succeeded*; speculative commands belong in a spec or research artifact, not here.
- **Don't duplicate `## Verify` content into `architecture.md` or `roadmap.md`.** They reference, they do not duplicate.
- **Don't write architecture rationale here.** The why behind the stack lives in `architecture.md` and the spec(s) that shaped it. Bootstrap records the *how to run it*.
- **Don't write task-level information here.** Per-task verification belongs in the task's `## Unit Test Strategy` section.
- **Don't append `## Change Logs` bullets without a markdown link.**
- **Don't manually archive the prior copy.** Archive on re-run is automated; manual moves break the audit trail.
