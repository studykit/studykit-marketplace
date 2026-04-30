# a4 — domain wiki authoring

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

`a4/domain.md` is the **shared vocabulary wiki**. It catalogs the cross-cutting concepts every UC, spec, and architecture component references — entities, value objects, lifecycle states. The domain page is downstream of UCs (concepts surface during interview) and upstream of architecture (components depend on the agreed vocabulary).

Companion to `./frontmatter-universals.md`, `./body-conventions.md`. Wiki pages share a minimal schema (`type:` + `updated:`) — the YAML below is the full contract.

## Frontmatter contract (do not deviate)

```yaml
---
type: domain
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `domain`.
- `updated:` is an unquoted ISO date. Bump on every edit.
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Concepts`, `## Relationships`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Concepts` — glossary of the domain entities, value objects, and significant terms. Each entry includes a name, a one-paragraph definition, and (optionally) examples or invariants. Concepts are the terms UC bodies, spec bodies, and architecture component names must use consistently.

**Optional, emit only when applicable:**

- `## Relationships` — how concepts relate (associations, compositions, aggregates). Skip when concepts are independent and the relationship is obvious from definitions alone.
- `## State Transitions` — for concepts whose lifecycle has named states, the transition graph (state, allowed next states, trigger). Common for entities tracked by the workspace (a `Session`'s state, a `Document`'s revision).
- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained. Concept definitions often link back to the UCs that introduced them (`[usecase/3-search-history](usecase/3-search-history.md)`).

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — added concept Foo
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — renamed Conversation → Session
```

Create the section if absent. The drift detector checks for `domain` ↔ `architecture` term consistency: if a concept appears in `architecture.md` `## Components` but is missing from `domain.md` `## Concepts`, a `kind: gap` review item is emitted.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Concepts`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename — the `type:` value must equal the file basename.

## Don't

- **Don't put architecture component definitions here.** Components live in `architecture.md`'s `## Components` section. Concepts are the user-domain vocabulary; components are the runtime shape.
- **Don't put framework-mandated terms here.** "Controller", "Repository", "DAO" are framework constructs, not domain concepts. They belong in `architecture.md`.
- **Don't rename a concept silently.** Renames cascade to UCs, specs, architecture, and code. Open a review item to manage the cascade if the rename surface is large.
- **Don't append `## Change Logs` bullets without a markdown link.** The link is what powers drift detection.
- **Don't pack relationship or state diagrams inline as long prose.** Use mermaid / ASCII / table form; keep prose to invariants the diagram does not capture.
