# a4 — context wiki authoring

`a4/context.md` is the **upstream framing wiki**. It records the original idea, the problem framing the workspace is shaped around, and (optionally) the screen-navigation narrative that ties UI use cases together. Every other wiki page and every issue family indirectly assumes the framing this page captures.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: context
updated: YYYY-MM-DD
---
```

- `type:` must be exactly `context`.
- `updated:` is an unquoted ISO date. Bump on every edit (including `<change-logs>` bullet appends and screen-group additions).
- Wiki pages have no `id`, no `status`, no `<log>`, no lifecycle.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks (lowercase + kebab-case), with markdown content between the open and close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

**Required:**

- `<original-idea>` — the user's input, captured **verbatim** at workspace creation. Do not paraphrase. Subsequent edits append follow-up clarifications as new paragraphs; the original quote stays.
- `<problem-framing>` — the shape the team commits to working on: who has the problem, what current solution is failing, what success looks like at a coarse level. Refined progressively over the workspace lifetime.

**Optional, emit only when applicable:**

- `<screens>` — for projects with UI use cases, the screen-navigation narrative grouping UCs into screens. Each screen block lists the screen slug (also added to UC `labels:`) and the UCs that participate, with markdown links. Skip for headless, non-UI, or single-screen projects.
- `<change-logs>` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown kebab-case tags are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained (e.g., `[usecase/3-search-history](usecase/3-search-history.md)`). The `<screens>` section in particular relies on these links.

## `<change-logs>` discipline

```markdown
<change-logs>

- YYYY-MM-DD — [usecase/<id>-<slug>](usecase/<id>-<slug>.md) — <what changed>
- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — <what changed>

</change-logs>
```

Create the section if absent. The wiki close guard surfaces missing bullets when a review item with `wiki_impact: [context]` transitions to `resolved`.

## Common mistakes

- **Stray content outside section blocks**.
- **Required section missing** (`<original-idea>`, `<problem-framing>`).
- **Inline or attribute-bearing tags**.
- **Same-tag nesting**.
- **H1 in body**. Page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

## Don't

- **Don't paraphrase `<original-idea>`.** It is the verbatim user input. Edits append; the original block stays.
- **Don't write detailed UC flows here.** Use cases live in `a4/usecase/<id>-<slug>.md`. `context.md` carries framing only.
- **Don't put domain concepts here.** Cross-cutting concepts belong in `domain.md`'s `<concepts>` section.
- **Don't write actor rosters here.** Actor definitions belong in `actors.md`'s `<roster>` section.
- **Don't pack screen mockups inline.** HTML mocks live under `a4/mock/<screen-slug>/`; reference them from `<screens>` if useful.
- **Don't append `<change-logs>` bullets without a markdown link.** The link is what powers the close-guard / drift checks.
