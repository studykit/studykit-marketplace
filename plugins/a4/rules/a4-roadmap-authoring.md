---
name: a4-roadmap-authoring
description: Authoring rules for the a4 roadmap wiki. Auto-loaded when reading or editing `a4/roadmap.md`.
paths: ["a4/roadmap.md"]
---

# a4 — roadmap wiki authoring guide

`a4/roadmap.md` is the **milestone narrative wiki**. It groups UCs
into milestones, names the dependency graph between them, and
records Shared Integration Points the architecture exposes. The
roadmap drives `/a4:run`'s cycle planning and the order
`task-implementer` agents pick up work.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship, cross-stage feedback, commit message form — live in
> [`a4-workspace-policies.md`](a4-workspace-policies.md) and load
> automatically alongside this rule. This rule covers the
> roadmap-wiki-specific contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit the roadmap wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md).

## How to author — always via `/a4:roadmap`

Do **not** hand-craft `roadmap.md` with `Write`. Always invoke
`/a4:roadmap` so the milestone narrative, dependency graph, and
Shared Integration Points are produced through the same flow. The
skill has a forward draft mode (always writes new tasks at
`pending` — batch fill-queue intent) and an iterate mode for
revisions.

If you must read the file to answer a question, prefer
`extract_section.py a4/roadmap.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — who can edit this page

Per `references/wiki-authorship.md`:

- **`/a4:roadmap` is the primary author.** Owns all body sections.
  In-situ edits from `/a4:roadmap` are unrestricted within the
  `<plan>` section.
- **No other skill edits in-situ.** `/a4:run` reads the roadmap; it
  never writes to it. Architecture changes that affect the roadmap
  flow back through `/a4:arch iterate` first, then a `/a4:roadmap
  iterate` pass picks up the resulting `target: roadmap` review
  items.
- The cross-stage stop/continue policy makes `/a4:roadmap` **stop**
  on architecture or UC issues — strong dependency. Do not write a
  partial roadmap that depends on unresolved upstream issues.

If you find yourself wanting to edit `roadmap.md` from any context
other than `/a4:roadmap`, **stop** and emit the review item instead.

## Frontmatter contract (do not deviate)

```yaml
---
type: roadmap
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `roadmap`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings
inside sections freely.

**Required (enforced by `body_schemas/roadmap.xsd`):**

- `<plan>` — the entire roadmap content lives in this single section,
  organized internally with H3+ headings:
  - **Milestone narrative.** What each milestone delivers, in user
    terms (links to the UCs it ships).
  - **Dependency graph.** Which milestones depend on which (mermaid
    or table form). Reflects UC `depends_on:` and architecture
    Shared Integration Points.
  - **Shared Integration Points.** Architecture interfaces that
    multiple milestones touch — typically named with markdown links
    into `architecture.md` `<components>`.
  - **Launch & Verify pointer.** A one-line link pointing at
    `bootstrap.md` (`See [bootstrap](bootstrap.md) for environment
    setup, build commands, and the verified smoke test.`). **No
    Launch & Verify content lives here** — `bootstrap.md` is the
    single source of truth and `/a4:run`, `task-implementer`, and
    `test-runner` read it directly.

**Optional:**

- `<change-logs>` — append-only audit trail of why this page was
  edited (dated bullets with markdown links to the causing UC,
  review item, or spec).

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained.
Every UC reference in the milestone narrative and every architecture
component reference in Shared Integration Points uses this form.

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — milestone-2 reshaped after arch fix
- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added to milestone-3

</change-logs>
```

Create the section if absent. The wiki close guard surfaces missing
bullets when a review item with `wiki_impact: [roadmap]` transitions
to `resolved`.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<plan>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file
  basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file roadmap.md
```

## Don't

- **Don't edit from any skill other than `/a4:roadmap`.** Emit a
  review item with `target: roadmap`.
- **Don't write Launch & Verify content here.** A one-line link to
  `bootstrap.md` is the contract — `/a4:run` and `task-implementer`
  read bootstrap directly.
- **Don't write a partial roadmap on a stopped flow.** When
  `/a4:roadmap` Step 4 halts on an architecture or UC issue, do not
  write `roadmap.md`. The review item plus a wrap-up message
  redirecting the user to `/a4:arch iterate` (or `/a4:usecase
  iterate`) is the right hand-off.
- **Don't define new architecture components here.** Components
  live in `architecture.md`. The roadmap references them.
- **Don't author tasks here.** Tasks live in `a4/task/<id>-<slug>.md`
  and are written by `/a4:roadmap` (batch) or `/a4:task` (single).
  The roadmap names milestones; tasks deliver them.
- **Don't pack architecture rationale.** Decisions belong in specs;
  the architecture page records the *current* shape; the roadmap
  records the *delivery sequence*.
- **Don't append `<change-logs>` bullets without a markdown link.**

## After authoring

`/a4:roadmap` does not commit; the file (plus any task files written
in the batch) is left in the working tree. The natural next step is
`/a4:run` to start the implement + test loop on the now-`pending`
task set.

When upstream wikis change substantially (architecture component
swap, UC additions), suggest `/a4:roadmap iterate` to refresh the
milestone narrative and dependency graph.

## Cross-references

- [`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) —
  full field schema, body-section table, validator behavior.
- [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) —
  primary-author table; `/a4:roadmap`-stops policy on upstream
  issues.
- [`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md) —
  tag form, link form, `<change-logs>` rules.
- [`skills/roadmap/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/roadmap/SKILL.md) —
  the authoring skill itself.
- `body_schemas/roadmap.xsd` — the source of truth for required vs
  optional sections.
