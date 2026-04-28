---
name: a4-actors-authoring
description: Authoring rules for the a4 actors wiki. Auto-loaded when reading or editing `a4/actors.md`.
paths: ["a4/actors.md"]
---

# a4 — actors wiki authoring guide

`a4/actors.md` is the **actor roster wiki**. It defines every person
or system actor that UCs reference via `actors: [<slug>]`. The roster
is the single source of truth for actor slugs — UC frontmatter is
validated against it, and `compass` derives the Authorization Matrix
view from it.

> **Workspace-wide policies** — writer-owned fields, id allocation,
> path-reference form, tag form, `<change-logs>` discipline, wiki
> authorship, cross-stage feedback, commit message form — live in
> [`a4-workspace-policies.md`](a4-workspace-policies.md) and load
> automatically alongside this rule. This rule covers the
> actors-wiki-specific contract on top.

This rule is the working contract for any LLM about to read, draft, or
edit the actors wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](../references/frontmatter-schema.md).

## How to author — always via `/a4:usecase` (or `/a4:arch` for system actors only)

Do **not** hand-craft `actors.md` with `Write`. Always invoke
`/a4:usecase` so new actor entries are confirmed with the user, slugs
are derived consistently, and the roster table stays referentially
intact for `actors:` lists in UC frontmatter.

If you must read the file to answer a question, prefer
`extract_section.py a4/actors.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — who can edit this page

Per `references/wiki-authorship.md`:

- **`/a4:usecase` is the primary author.** Owns all roster entries.
  In-situ edits from `/a4:usecase` are unrestricted.
- **`/a4:arch` may add a `system`-type actor** that surfaces during
  component design (privilege/description text only; never modify a
  `person`-type actor). The justification is symmetric with the
  `/a4:domain` cross-edit allowance — system actors often only emerge
  during architectural work, and forcing them through review-item
  friction is wasteful.
- All other skills emit review items with `target: actors`.

If you find yourself wanting to edit `actors.md` from any context
other than the two above, **stop** and emit the review item instead.

## Frontmatter contract (do not deviate)

```yaml
---
type: actors
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `actors`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings
inside sections freely.

**Required (enforced by `body_schemas/actors.xsd`):**

- `<roster>` — the actor table. One row per actor with these columns:
  - **Slug** — kebab-case identifier (e.g., `meeting-organizer`,
    `team-member`, `platform`). This is what UC frontmatter
    `actors: [<slug>]` references.
  - **Type** — `person` or `system`.
  - **Role / privileges** — what this actor is allowed to do; the
    privilege level relative to other actors.
  - **Description** — a short prose paragraph explaining who this
    actor is.

**Optional:**

- `<change-logs>` — append-only audit trail of why this page was
  edited (dated bullets with markdown links to the causing UC,
  review item, or spec).

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Slug discipline

Actor slugs are referenced from UC frontmatter `actors:` lists.
Renaming a slug breaks every UC that references it. **Always treat a
rename as a structural change** and open a review item explaining
the cascade — even when the rename feels obvious. Single in-situ
renames from `/a4:usecase` are acceptable when the impact is one or
two UCs, but document the rename in `<change-logs>` linking the
review item that motivated it.

A new actor's slug should:

- Be lowercase, hyphen-separated.
- Match the user-facing role, not an implementation detail.
- Not collide with an existing slug. The validator does not currently
  enforce uniqueness; visual review during `/a4:usecase` is the gate.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained
(e.g., the description column may link to representative UCs:
`[usecase/3-search-history](usecase/3-search-history.md)`).

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added actor team-member
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — renamed admin → workspace-admin

</change-logs>
```

Create the section if absent. Drift detection cross-checks UC
`actors:` lists against the roster — a UC referencing an unknown slug
emits a `kind: finding` review item.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<roster>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file
  basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file actors.md
```

## Don't

- **Don't edit from any skill other than `/a4:usecase` or `/a4:arch`
  (system actors only).** Emit a review item with `target: actors`.
- **Don't modify a `person`-type row from `/a4:arch`.** Person actors
  are user-facing; only `/a4:usecase` knows their full context.
- **Don't rename a slug without a review item** when the cascade
  touches more than one or two UCs.
- **Don't put authorization rules here as prose.** The roster carries
  privilege levels; per-UC authorization is encoded in UC `<flow>` /
  `<validation>` (and in `architecture.md` for technical enforcement
  details).
- **Don't pack actor backstories.** The description column is one
  paragraph. Longer narratives belong in `context.md`'s
  `<problem-framing>`.
- **Don't append `<change-logs>` bullets without a markdown link.**

## After authoring

`/a4:usecase` does not commit; the file is left in the working tree.
A roster change typically lands alongside a UC change that
introduced or renamed the actor; commit them together.

## Cross-references

- [`references/frontmatter-schema.md §Wiki pages`](../references/frontmatter-schema.md) —
  full field schema, body-section table, validator behavior.
- [`references/wiki-authorship.md`](../references/wiki-authorship.md) —
  primary-author table; `/a4:arch`'s system-actor allowance.
- [`references/body-conventions.md`](../references/body-conventions.md) —
  tag form, link form, `<change-logs>` rules.
- [`skills/usecase/SKILL.md`](../skills/usecase/SKILL.md) —
  Step 2's actor-discovery flow.
- `body_schemas/actors.xsd` — the source of truth for required vs
  optional sections.
