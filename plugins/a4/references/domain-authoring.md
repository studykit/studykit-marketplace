# a4 — domain wiki authoring

`a4/domain.md` is the **shared vocabulary wiki**. It catalogs the cross-cutting concepts every UC, spec, and architecture component references — entities, value objects, lifecycle states. The domain page is downstream of UCs (concepts surface during interview) and upstream of architecture (components depend on the agreed vocabulary).

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Reading the file

If only a specific section is needed to answer a question, prefer `extract_section.py a4/domain.md <tag>` over loading the whole markdown.

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

The body is a sequence of column-0 `<section>...</section>` blocks (lowercase + kebab-case), with markdown content between the open and close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required (enforced by `../scripts/body_schemas/domain.xsd`):**

- `<concepts>` — glossary of the domain entities, value objects, and significant terms. Each entry includes a name, a one-paragraph definition, and (optionally) examples or invariants. Concepts are the terms UC bodies, spec bodies, and architecture component names must use consistently.

**Optional, emit only when applicable:**

- `<relationships>` — how concepts relate (associations, compositions, aggregates). Skip when concepts are independent and the relationship is obvious from definitions alone.
- `<state-transitions>` — for concepts whose lifecycle has named states, the transition graph (state, allowed next states, trigger). Common for entities tracked by the workspace (a `Session`'s state, a `Document`'s revision).
- `<change-logs>` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Concept definitions often link back to the UCs that introduced them (`[usecase/3-search-history](usecase/3-search-history.md)`).

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added concept Foo
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — renamed Conversation → Session

</change-logs>
```

Create the section if absent. The drift detector checks for `domain` ↔ `architecture` term consistency: if a concept appears in `architecture.md` `<components>` but is missing from `domain.md` `<concepts>`, a `kind: gap` review item is emitted.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<concepts>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file domain.md
```

## Don't

- **Don't put architecture component definitions here.** Components live in `architecture.md`'s `<components>` section. Concepts are the user-domain vocabulary; components are the runtime shape.
- **Don't put framework-mandated terms here.** "Controller", "Repository", "DAO" are framework constructs, not domain concepts. They belong in `architecture.md`.
- **Don't rename a concept silently.** Renames cascade to UCs, specs, architecture, and code. Open a review item to manage the cascade if the rename surface is large.
- **Don't append `<change-logs>` bullets without a markdown link.** The link is what powers drift detection.
- **Don't pack relationship or state diagrams inline as long prose.** Use mermaid / ASCII / table form; keep prose to invariants the diagram does not capture.
