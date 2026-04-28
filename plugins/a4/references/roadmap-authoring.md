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
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks (lowercase + kebab-case), with markdown content between the open and close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `<plan>` — the entire roadmap content lives in this single section, organized internally with H3+ headings:
  - **Milestone narrative.** What each milestone delivers, in user terms (links to the UCs it ships).
  - **Dependency graph.** Which milestones depend on which (mermaid or table form). Reflects UC `depends_on:` and architecture Shared Integration Points.
  - **Shared Integration Points.** Architecture interfaces that multiple milestones touch — typically named with markdown links into `architecture.md` `<components>`.
  - **Launch & Verify pointer.** A one-line link pointing at `bootstrap.md` (`See [bootstrap](bootstrap.md) for environment setup, build commands, and the verified smoke test.`). **No Launch & Verify content lives here** — `bootstrap.md` is the single source of truth.

**Optional:**

- `<change-logs>` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown kebab-case tags are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Every UC reference in the milestone narrative and every architecture component reference in Shared Integration Points uses this form.

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — milestone-2 reshaped after arch fix
- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added to milestone-3

</change-logs>
```

Create the section if absent. The wiki close guard surfaces missing bullets when a review item with `wiki_impact: [roadmap]` transitions to `resolved`.

## Common mistakes

- **Stray content outside section blocks**.
- **Required section missing** (`<plan>`).
- **Inline or attribute-bearing tags**.
- **Same-tag nesting**.
- **H1 in body**. Page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

## Don't

- **Don't write Launch & Verify content here.** A one-line link to `bootstrap.md` is the contract.
- **Don't define new architecture components here.** Components live in `architecture.md`. The roadmap references them.
- **Don't author tasks here.** Tasks live in `a4/task/<id>-<slug>.md`. The roadmap names milestones; tasks deliver them.
- **Don't pack architecture rationale.** Decisions belong in specs; the architecture page records the *current* shape; the roadmap records the *delivery sequence*.
- **Don't append `<change-logs>` bullets without a markdown link.**
