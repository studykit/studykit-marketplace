# a4 — context wiki authoring

`a4/context.md` is the **upstream framing wiki**. It records the original idea, the problem framing the workspace is shaped around, and (optionally) the screen-navigation narrative that ties UI use cases together. Every other wiki page and every issue family indirectly assumes the framing this page captures.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`. Wiki pages share a minimal schema (`type:` + `updated:`) — the YAML below is the full contract.

## Frontmatter contract (do not deviate)

```yaml
---
type: context
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `context`.
- `updated:` is an unquoted ISO date. Bump on every edit (including `## Change Logs` bullet appends and screen-group additions).
- Wiki pages have no `id`, no `status`, no `## Log`, no lifecycle.

## Body shape

The body is a sequence of column-0 H2 headings in Title Case (e.g., `## Original Idea`, `## Problem Framing`), with markdown content following each heading until the next H2 or end of file. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `## Original Idea` — the user's input, captured **verbatim** at workspace creation. Do not paraphrase. Subsequent edits append follow-up clarifications as new paragraphs; the original quote stays.
- `## Problem Framing` — the shape the team commits to working on: who has the problem, what current solution is failing, what success looks like at a coarse level. Refined progressively over the workspace lifetime.

**Optional, emit only when applicable:**

- `## Screens` — for projects with UI use cases, the screen-navigation narrative grouping UCs into screens. Each screen block lists the screen slug (also added to UC `labels:`) and the UCs that participate, with markdown links. Skip for headless, non-UI, or single-screen projects.
- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained (e.g., `[usecase/3-search-history](usecase/3-search-history.md)`). The `## Screens` section in particular relies on these links.

## `## Change Logs` discipline

```markdown
## Change Logs

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — <what changed>
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — <what changed>
```

Create the section if absent. The wiki close guard surfaces missing bullets when a review item whose `target:` lists `context` transitions to `resolved`.

## Common mistakes

- **Stray content above the first H2 heading**.
- **Required section missing** (`## Original Idea`, `## Problem Framing`).
- **H2 not in column 0 or not Title Case**.
- **Sections nested inside other sections** — every section sits at the body's top level.
- **H1 in body**. Page name is the file basename; title is frontmatter-only.
- **`type:` mismatch** with filename — the `type:` value must equal the file basename.

## Don't

- **Don't paraphrase `## Original Idea`.** It is the verbatim user input. Edits append; the original block stays.
- **Don't write detailed UC flows here.** Use cases live in `a4/usecase/<id>-<slug>.md`. `context.md` carries framing only.
- **Don't put domain concepts here.** Cross-cutting concepts belong in `domain.md`'s `## Concepts` section.
- **Don't write actor rosters here.** Actor definitions belong in `actors.md`'s `## Roster` section.
- **Don't pack screen mockups inline.** HTML mocks live under `a4/mock/<screen-slug>/`; reference them from `## Screens` if useful.
- **Don't append `## Change Logs` bullets without a markdown link.** The link is what powers the close-guard / drift checks.
