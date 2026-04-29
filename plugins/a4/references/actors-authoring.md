# a4 — actors wiki authoring

`a4/actors.md` is the **actor roster wiki**. It defines every person or system actor that UCs reference via `actors: [<slug>]`. The roster is the single source of truth for actor slugs — UC frontmatter is validated against it.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: actors
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `actors`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Roster`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Roster` — the actor table. One row per actor with these columns:
  - **Slug** — kebab-case identifier (e.g., `meeting-organizer`, `team-member`, `platform`). This is what UC frontmatter `actors: [<slug>]` references.
  - **Type** — `person` or `system`.
  - **Role / privileges** — what this actor is allowed to do; the privilege level relative to other actors.
  - **Description** — a short prose paragraph explaining who this actor is.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Slug discipline

Actor slugs are referenced from UC frontmatter `actors:` lists. Renaming a slug breaks every UC that references it. **Always treat a rename as a structural change** and open a review item explaining the cascade — even when the rename feels obvious.

A new actor's slug should:

- Be lowercase, hyphen-separated.
- Match the user-facing role, not an implementation detail.
- Not collide with an existing slug. The validator does not currently enforce uniqueness; visual review at edit time is the gate.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained (e.g., the description column may link to representative UCs: `[usecase/3-search-history](usecase/3-search-history.md)`).

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added actor team-member
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — renamed admin → workspace-admin
```

Create the section if absent. Drift detection cross-checks UC `actors:` lists against the roster — a UC referencing an unknown slug emits a `kind: finding` review item.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Roster`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename → frontmatter validator error.

## Don't

- **Don't rename a slug without a review item** when the cascade touches more than one or two UCs.
- **Don't put authorization rules here as prose.** The roster carries privilege levels; per-UC authorization is encoded in UC `## Flow` / `## Validation` (and in `architecture.md` for technical enforcement details).
- **Don't pack actor backstories.** The description column is one paragraph. Longer narratives belong in `context.md`'s `## Problem Framing`.
- **Don't append `## Change Logs` bullets without a markdown link.**
