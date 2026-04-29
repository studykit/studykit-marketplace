# a4 — roadmap wiki authoring

`a4/roadmap.md` is the **milestone narrative wiki**. It groups UCs into milestones, names the dependency graph between them, and records Shared Integration Points the architecture exposes.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: roadmap
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `roadmap`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Plan`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Plan` — the entire roadmap content lives in this single section, organized internally with H3+ headings:
  - **Milestone narrative.** What each milestone delivers, in user terms (links to the UCs it ships).
  - **Dependency graph.** Which milestones depend on which (mermaid or table form). Derived from each UC's `## Dependencies` body narrative, `task.depends_on:` chains, and architecture Shared Integration Points.
  - **Shared Integration Points.** Architecture interfaces that multiple milestones touch — typically named with markdown links into `architecture.md` `## Components`.
  - **Launch & Verify pointer.** A one-line link pointing at `bootstrap.md` (`See [bootstrap](bootstrap.md) for environment setup, build commands, and the verified smoke test.`). **No Launch & Verify content lives here** — `bootstrap.md` is the single source of truth.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Every UC reference in the milestone narrative and every architecture component reference in Shared Integration Points uses this form.

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — milestone-2 reshaped after arch fix
- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added to milestone-3
```

Create the section if absent. The wiki close guard surfaces missing bullets when a review item whose `target:` lists `roadmap` transitions to `resolved`.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Plan`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename → frontmatter validator error.

## Don't

- **Don't write Launch & Verify content here.** A one-line link to `bootstrap.md` is the contract.
- **Don't define new architecture components here.** Components live in `architecture.md`. The roadmap references them.
- **Don't author tasks here.** Tasks live in `a4/task/<id>-<slug>.md`. The roadmap names milestones; tasks deliver them.
- **Don't pack architecture rationale.** Decisions belong in specs; the architecture page records the *current* shape; the roadmap records the *delivery sequence*.
- **Don't append `## Change Logs` bullets without a markdown link.**
