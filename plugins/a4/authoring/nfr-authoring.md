# a4 — NFR wiki authoring

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

`a4/nfr.md` is the **non-functional requirements wiki**. It records performance targets, security requirements, scalability bounds, accessibility requirements, compliance constraints, and other cross-cutting properties that affect every UC and architecture decision. NFRs are optional — small or exploratory projects may have none, in which case the file simply does not exist.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`. Wiki pages share a minimal schema (`type:` + `updated:`) — the YAML below is the full contract.

## Frontmatter contract (do not deviate)

```yaml
---
type: nfr
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `nfr`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Requirements`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Requirements` — the NFR table. One row per requirement with these columns:
  - **Description** — the requirement in prose (e.g., "Cold-start response under 200 ms p95").
  - **Affected UCs** — markdown links to UCs the requirement constrains (e.g., `[usecase/3-search-history](usecase/3-search-history.md)`). Use `(all)` when the requirement applies workspace-wide.
  - **Measurable criteria** — the concrete threshold or check (timing, error rate, compliance standard reference). Avoid aspirational phrasing — NFRs only earn their slot when they have a measurable shape.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. The Affected UCs column relies entirely on this form.

Architecture footnote annotations may attach to an existing NFR row to point at the architecture decision that satisfies it:

```markdown
- Cold-start response under 200 ms p95 — [usecase/3](usecase/3-search-history.md), [usecase/5](usecase/5-render-mock.md) — p95 < 200 ms across all responses[^1]

[^1]: Addressed by SessionService caching layer — see [architecture#SessionService](architecture.md#sessionservice).
```

The footnote points at the architecture decision that satisfies the NFR. Do not introduce footnotes that edit the requirement text itself.

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added latency NFR
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — refined p95 threshold
```

Create the section if absent.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Requirements`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename — the `type:` value must equal the file basename.

## Don't

- **Don't write aspirational requirements without a measurable criterion.** "Should be fast" is not an NFR. "p95 < 200 ms" is.
- **Don't list functional behavior here.** Functional requirements belong in UCs (`## Flow`, `## Validation`, `## Error Handling`). NFRs are cross-cutting properties.
- **Don't put implementation strategies here.** "We will use Redis for caching" belongs in `architecture.md`. The NFR is the target; the architecture page records the response.
- **Don't append `## Change Logs` bullets without a markdown link.**
