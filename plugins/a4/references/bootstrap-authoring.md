# a4 — bootstrap wiki authoring

`a4/bootstrap.md` is the **single source of truth for Launch & Verify**. It records the environment setup, the build/launch commands, and the verified smoke test that proves the workspace "runs". The `<verify>` section in particular is the executable verification contract — never duplicated into other wiki pages.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Reading the file

If only a specific section is needed to answer a question, prefer `extract_section.py a4/bootstrap.md <tag>` over loading the whole markdown.

## Frontmatter contract (do not deviate)

```yaml
---
type: bootstrap
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `bootstrap`.
- `updated:` is an unquoted ISO date. Bump on every re-run.
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks (lowercase + kebab-case), with markdown content between the open and close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required (enforced by `../scripts/body_schemas/bootstrap.xsd`):**

- `<environment>` — the runtime environment the workspace requires: language version, package manager, OS-specific notes, env vars needed at runtime. Discovered and recorded — not speculated.
- `<launch>` — the build / start commands, in order. Each command is the **literal** invocation that was verified to work, not a template. Distinguish dev / build / production where applicable.
- `<verify>` — **the executable verification contract.** Contains:
  - Verified test commands (unit, integration, e2e — whichever the project has).
  - The smoke scenario — what running the application from scratch should produce.
  - Test isolation flags — env vars, fixtures, or process flags needed to keep tests deterministic.

**Optional:**

- `<change-logs>` — append-only audit trail of why this page was re-derived (dated bullets with markdown links to the causing review item or architecture spec). Most edits to this page are full re-runs, so `<change-logs>` is sparse — record why a re-run was needed.

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Why `<verify>` lives only here

`<verify>` is the single executable contract that drives implementation verification. Duplicating it into `architecture.md` (test strategy section) or `roadmap.md` would create drift. Architecture's `<test-strategy>` describes the **strategy** (unit / integration / e2e split, isolation philosophy); bootstrap's `<verify>` records the **executable contract** (the actual commands). The two are complementary.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Bootstrap typically links back to `architecture.md` for context on why certain commands or env vars are required.

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — re-run after arch version-incompatibility fix
- YYYY-MM-DD — [spec/<id>-<slug>](spec/<id>-<slug>.md) — added smoke scenario for new component

</change-logs>
```

Create the section if absent. Most bullets cite a `target: architecture` review item that triggered the re-run.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<environment>`, `<launch>`, `<verify>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file bootstrap.md
```

## Don't

- **Don't write commands that have not been verified.** Bootstrap records what *succeeded*; speculative commands belong in a spec or research artifact, not here.
- **Don't duplicate `<verify>` content into `architecture.md` or `roadmap.md`.** They reference, they do not duplicate.
- **Don't write architecture rationale here.** The why behind the stack lives in `architecture.md` and the spec(s) that shaped it. Bootstrap records the *how to run it*.
- **Don't write task-level information here.** Per-task verification belongs in the task's `<unit-test-strategy>` section.
- **Don't append `<change-logs>` bullets without a markdown link.**
- **Don't manually archive the prior copy.** Archive on re-run is automated; manual moves break the audit trail.
