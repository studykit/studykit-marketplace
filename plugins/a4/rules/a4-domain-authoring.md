---
name: a4-domain-authoring
description: Authoring rules for the a4 domain wiki. Auto-loaded when reading or editing `a4/domain.md`.
paths: ["a4/domain.md"]
---

# a4 — domain wiki authoring guide

`a4/domain.md` is the **shared vocabulary wiki**. It catalogs the
cross-cutting concepts every UC, spec, and architecture component
references — entities, value objects, lifecycle states. The domain
page is downstream of UCs (concepts surface during interview) and
upstream of architecture (components depend on the agreed
vocabulary).

This rule is the working contract for any LLM about to read, draft, or
edit the domain wiki. The full schema lives in
[`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md);
authorship boundaries live in
[`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md);
body-tag mechanics live in
[`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md).
Read those before deviating from the rules below.

## How to author — always via `/a4:domain` (or `/a4:arch` for limited cases)

Do **not** hand-craft `domain.md` with `Write`. Always invoke
`/a4:domain` so concept extraction, relationship analysis, and state
transitions are produced through the same flow.

If you must read the file to answer a question, prefer
`extract_section.py a4/domain.md <tag>` over loading the whole
markdown (see `a4-section-enum.md`).

## Authorship — who can edit this page

Per `references/wiki-authorship.md`:

- **`/a4:domain` is the primary author.** Owns all body sections.
- **`/a4:arch` is allowed limited in-situ edits** when concept changes
  surface during component design. The b3 decision table in
  `skills/arch/SKILL.md` Phase 3 enumerates exactly what arch can
  change in-situ:
  - Add a new concept to `<concepts>` (definition wording is `arch`'s
    call when discovered during component design).
  - 1:1 rename (e.g., `Conversation → Session`) when the rename is
    obvious from the architectural context.
  - Adjust definition wording for an existing concept.
  - **Structural changes** (split / merge / new relationship / new
    state transition) are out of in-situ scope — emit a review item
    with `target: domain`, `wiki_impact: [domain]` and let
    `/a4:domain iterate` resolve it.
- All other skills emit review items with `target: domain`.

The split exists because term churn is normal during arch work and
forcing every rename through review-item friction is too costly. But
structural changes are too easy to get wrong without the domain
extraction lens, so they always go back to `/a4:domain`.

## Frontmatter contract (do not deviate)

```yaml
---
type: domain
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `domain`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings
inside sections freely.

**Required (enforced by `body_schemas/domain.xsd`):**

- `<concepts>` — glossary of the domain entities, value objects, and
  significant terms. Each entry includes a name, a one-paragraph
  definition, and (optionally) examples or invariants. Concepts are
  the terms UC bodies, spec bodies, and architecture component names
  must use consistently.

**Optional, emit only when applicable:**

- `<relationships>` — how concepts relate (associations,
  compositions, aggregates). Skip when concepts are independent and
  the relationship is obvious from definitions alone.
- `<state-transitions>` — for concepts whose lifecycle has named
  states, the transition graph (state, allowed next states, trigger).
  Common for entities tracked by the workspace (a `Session`'s state,
  a `Document`'s revision).
- `<change-logs>` — append-only audit trail of why this page was
  edited (dated bullets with markdown links to the causing UC,
  review item, or spec).

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained.
Concept definitions often link back to the UCs that introduced them
(`[usecase/3-search-history](usecase/3-search-history.md)`).

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added concept Foo
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — renamed Conversation → Session

</change-logs>
```

Create the section if absent. The drift detector checks for `domain`
↔ `architecture` term consistency: if a concept appears in
`architecture.md` `<components>` but is missing from `domain.md`
`<concepts>`, a `kind: gap` review item is emitted.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<concepts>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file
  basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file domain.md
```

## Don't

- **Don't edit from any skill other than `/a4:domain` or `/a4:arch`
  (limited).** Emit a review item with `target: domain`.
- **Don't make structural changes from `/a4:arch`.** Splits, merges,
  new relationships, new state transitions go back to `/a4:domain
  iterate` via a review item.
- **Don't put architecture component definitions here.** Components
  live in `architecture.md`'s `<components>` section. Concepts are
  the user-domain vocabulary; components are the runtime shape.
- **Don't put framework-mandated terms here.** "Controller",
  "Repository", "DAO" are framework constructs, not domain
  concepts. They belong in `architecture.md`.
- **Don't rename a concept silently.** Renames cascade to UCs,
  specs, architecture, and code. Open a review item to manage the
  cascade if the rename surface is large.
- **Don't append `<change-logs>` bullets without a markdown link.**
  The link is what powers drift detection.
- **Don't pack relationship or state diagrams inline as long
  prose.** Use mermaid / ASCII / table form; keep prose to
  invariants the diagram does not capture.

## After authoring

`/a4:domain` does not commit; the file is left in the working tree.
Substantial concept changes typically warrant `/a4:arch iterate` to
propagate component renames or new component additions, plus
`/a4:usecase iterate` if the rename touches UC body terminology.

## Cross-references

- [`references/frontmatter-schema.md §Wiki pages`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) —
  full field schema, body-section table, validator behavior.
- [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) —
  why domain has a limited-shared in-situ edit allowance with
  architecture; the structural-change boundary.
- [`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md) —
  tag form, link form, `<change-logs>` rules.
- [`skills/domain/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/domain/SKILL.md) —
  the primary authoring skill.
- [`skills/arch/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/arch/SKILL.md) —
  Phase 3 b3 decision table for in-situ domain edits from arch.
- `body_schemas/domain.xsd` — the source of truth for required vs
  optional sections.
