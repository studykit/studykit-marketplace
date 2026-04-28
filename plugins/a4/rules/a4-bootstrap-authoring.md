---
name: a4-bootstrap-authoring
description: Authoring rules for the a4 bootstrap wiki. Auto-loaded when reading or editing `a4/bootstrap.md`.
paths: ["a4/bootstrap.md"]
---

# a4 — bootstrap wiki authoring guide

`a4/bootstrap.md` is the **single source of truth for Launch &
Verify**. It records the environment setup, the build/launch
commands, and the verified smoke test that proves the workspace
"runs". The `<verify>` section in particular is read directly by
`/a4:run`, `task-implementer`, and `test-runner` — never duplicated
into other wiki pages.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship, cross-stage feedback, commit message form — live in
> [`a4-workspace-policies.md`](a4-workspace-policies.md) and load
> automatically alongside this rule. This rule covers the
> bootstrap-wiki-specific contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit the bootstrap wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](../references/frontmatter-schema.md).

## How to author — always via `/a4:auto-bootstrap`

Do **not** hand-craft `bootstrap.md` with `Write`. Always invoke
`/a4:auto-bootstrap` so the environment is actually executed (not
just described), the commands are verified to succeed, and prior
copies are archived rather than overwritten.

The skill writes `bootstrap.md` after running the verification
sequence end-to-end. If verification fails on an architecture issue,
the skill **continues** with a partial result (per the cross-stage
stop/continue policy) and emits a `target: architecture` review item
to be resolved via `/a4:arch iterate`. After a substantial
architecture change, re-run `/a4:auto-bootstrap` to re-verify.

If you must read the file to answer a question, prefer
`extract_section.py a4/bootstrap.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — who can edit this page

Per `references/wiki-authorship.md`:

- **`/a4:auto-bootstrap` is the only writer.** It owns all body
  sections; re-runs archive the prior copy and write a fresh version.
- **No other skill edits in-situ.** Editing `bootstrap.md` by hand
  defeats the verification contract — the section names commands
  asserted to have run successfully on the recorded environment, and
  hand-edits that bypass verification produce stale or wrong
  contracts that `/a4:run` then trusts.

If you find yourself wanting to edit `bootstrap.md` from any context
other than `/a4:auto-bootstrap`, **stop** and re-run the skill (or
emit a `target: bootstrap` review item if the issue is conceptual
rather than verification-driven — these are rare; most bootstrap
issues are actually architecture issues that `auto-bootstrap` re-runs
will correct).

## Frontmatter contract (do not deviate)

```yaml
---
type: bootstrap
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `bootstrap`.
- `updated:` is an unquoted ISO date. The skill bumps it on every
  re-run.
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings
inside sections freely.

**Required (enforced by `body_schemas/bootstrap.xsd`):**

- `<environment>` — the runtime environment the workspace requires:
  language version, package manager, OS-specific notes, env vars
  needed at runtime. Discovered and recorded by the skill, not
  speculated.
- `<launch>` — the build / start commands, in order. Each command is
  the **literal** invocation that was verified to work, not a
  template. Distinguish dev / build / production where applicable.
- `<verify>` — **the single source of truth for verification.** This
  section is read directly by `/a4:run`, `task-implementer`, and
  `test-runner`. It contains:
  - Verified test commands (unit, integration, e2e — whichever the
    project has).
  - The smoke scenario — what running the application from scratch
    should produce.
  - Test isolation flags — env vars, fixtures, or process flags
    needed to keep tests deterministic.

**Optional:**

- `<change-logs>` — append-only audit trail of why this page was
  re-derived (dated bullets with markdown links to the causing review
  item or architecture spec). Most edits to this page are full
  re-runs, so `<change-logs>` is sparse — the skill records why a
  re-run was needed.

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Why `<verify>` lives only here

`<verify>` is read by three downstream consumers:

- `/a4:run` — to drive the implement + test loop's verification
  step.
- `task-implementer` — to confirm tests pass before transitioning
  the task to `complete`.
- `test-runner` — to invoke the right test commands per task.

Duplicating `<verify>` content into `architecture.md` (test
strategy section) or `roadmap.md` would create drift. Architecture's
`<test-strategy>` describes the **strategy** (unit / integration /
e2e split, isolation philosophy); bootstrap's `<verify>` records the
**executable contract** (the actual commands). The two are
complementary.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained.
Bootstrap typically links back to `architecture.md` for context on
why certain commands or env vars are required.

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — re-run after arch version-incompatibility fix
- YYYY-MM-DD — [spec/<id>-<slug>](spec/<id>-<slug>.md) — added smoke scenario for new component

</change-logs>
```

Create the section if absent. Most bullets cite a `target:
architecture` review item that triggered the re-run.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<environment>`, `<launch>`,
  `<verify>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file
  basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file bootstrap.md
```

## Don't

- **Don't edit from any skill other than `/a4:auto-bootstrap`.**
  Re-run the skill, or emit a `target: bootstrap` review item if the
  issue is conceptual.
- **Don't write commands that have not been verified.** Bootstrap
  records what *succeeded*; speculative commands belong in a spec or
  research artifact, not here.
- **Don't duplicate `<verify>` content into `architecture.md` or
  `roadmap.md`.** They reference, they do not duplicate.
- **Don't write architecture rationale here.** The why behind the
  stack lives in `architecture.md` and the spec(s) that shaped it.
  Bootstrap records the *how to run it*.
- **Don't write task-level information here.** Per-task verification
  belongs in the task's `<unit-test-strategy>` section.
- **Don't append `<change-logs>` bullets without a markdown link.**
- **Don't manually archive the prior copy.** The skill handles
  archive on re-run; manual moves break the audit trail.

## After authoring

`/a4:auto-bootstrap` does not commit; the file is left in the working
tree along with any review items the verification surfaced. When
`<verify>` content has changed, the natural next steps are
`/a4:roadmap iterate` (refresh the Launch & Verify pointer if the
shape changed) and `/a4:run` (resume implementation against the
re-verified environment).

## Cross-references

- [`references/frontmatter-schema.md §Wiki pages`](../references/frontmatter-schema.md) —
  full field schema, body-section table, validator behavior.
- [`references/wiki-authorship.md`](../references/wiki-authorship.md) —
  primary-author table; bootstrap's single-owner rule and
  continue-with-review-item policy on architecture issues.
- [`references/body-conventions.md`](../references/body-conventions.md) —
  tag form, link form, `<change-logs>` rules.
- [`skills/auto-bootstrap/SKILL.md`](../skills/auto-bootstrap/SKILL.md) —
  the authoring skill itself; verification sequence and archive
  semantics.
- `body_schemas/bootstrap.xsd` — the source of truth for required vs
  optional sections.
