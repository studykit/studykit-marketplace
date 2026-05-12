# a4 — actors wiki authoring

`a4/actors.md` is the **actor roster wiki**. It defines every person or system actor that UCs reference via `actors: [<slug>]`. The roster is the single source of truth for actor slugs — UC frontmatter is validated against it.

Frontmatter contract: `./frontmatter-wiki.md`. Body conventions: `./wiki-body.md` (`## Change Logs`, Wiki Update Protocol).

## Body shape

**Required:**

- `## Roster` — the actor table. One row per actor:
  - **Slug** — kebab-case identifier (e.g., `meeting-organizer`, `team-member`, `platform`). Referenced from UC frontmatter `actors: [<slug>]`.
  - **Type** — `person` or `system`.
  - **Role / privileges** — what this actor is allowed to do; the privilege level relative to other actors.
  - **Description** — short prose paragraph explaining who this actor is.

**Optional:**

- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with backlinks to the causing UC, review item, or spec). Format: `./wiki-body.md`.

Unknown H2 headings are tolerated.

### Slug discipline

Actor slugs are referenced from UC frontmatter `actors:` lists. Renaming a slug breaks every UC that references it. **Always treat a rename as a structural change** and open a review item explaining the cascade — even when the rename feels obvious.

A new actor's slug should:

- Match the user-facing role, not an implementation detail.
- Not collide with an existing slug. Uniqueness is not currently enforced automatically; visual review at edit time is the gate.

## Drift detection

Drift detection cross-checks UC `actors:` lists against the roster — a UC referencing an unknown slug emits a `kind: finding` review item.

## Common mistakes (actors-specific)

- **Required section missing** (`## Roster`).

## Don't

- **Don't rename a slug without a review item** when the cascade touches more than one or two UCs.
- **Don't put authorization rules here as prose.** The roster carries privilege levels; per-UC authorization is encoded in UC `## Flow` / `## Validation` (and in `architecture.md` for technical enforcement details).
- **Don't pack actor backstories.** The description column is one paragraph. Longer narratives belong in `context.md`'s `## Problem Framing`.
- **Don't append `## Change Logs` bullets without a backlink path.**
