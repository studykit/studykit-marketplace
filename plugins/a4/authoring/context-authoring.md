# a4 — context wiki authoring

`a4/context.md` is the **upstream framing wiki**. It records the original idea, the problem framing the workspace is shaped around, and (optionally) the screen-navigation narrative that ties UI use cases together. Every other wiki page and every issue family indirectly assumes the framing this page captures.

Frontmatter contract: see `./frontmatter-universals.md` § Wiki family. Body conventions: see `./wiki-body.md` (`## Change Logs`, Wiki Update Protocol). Bump `updated:` on every edit (including `## Change Logs` bullet appends and screen-group additions).

## Body shape

**Required:**

- `## Original Idea` — the user's input, captured **verbatim** at workspace creation. Do not paraphrase. Subsequent edits append follow-up clarifications as new paragraphs; the original quote stays.
- `## Problem Framing` — the shape the team commits to working on: who has the problem, what current solution is failing, what success looks like at a coarse level. Refined progressively over the workspace lifetime.

**Optional, emit only when applicable:**

- `## Screens` — for projects with UI use cases, the screen-navigation narrative grouping UCs into screens. Each screen block lists the screen slug (also added to UC `labels:`) and the UCs that participate, with markdown links. Skip for headless, non-UI, or single-screen projects.
- `## Change Logs` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec). Format and discipline: `./wiki-body.md`.

Unknown H2 headings are tolerated.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained (e.g., `[usecase/3-search-history](usecase/3-search-history.md)`). The `## Screens` section in particular relies on these links.

## Change Log triggers

The wiki close guard surfaces missing bullets when a review item whose `target:` lists `context` transitions to `resolved`.

## Common mistakes (context-specific)

- **Required section missing** (`## Original Idea`, `## Problem Framing`).

## Don't

- **Don't paraphrase `## Original Idea`.** It is the verbatim user input. Edits append; the original block stays.
- **Don't write detailed UC flows here.** Use cases live in `a4/usecase/<id>-<slug>.md`. `context.md` carries framing only.
- **Don't put domain concepts here.** Cross-cutting concepts belong in `domain.md`'s `## Concepts` section.
- **Don't write actor rosters here.** Actor definitions belong in `actors.md`'s `## Roster` section.
- **Don't pack screen mockups inline.** HTML mocks live under `a4/mock/<screen-slug>/`; reference them from `## Screens` if useful.
- **Don't append `## Change Logs` bullets without a markdown link.** The link is what makes the bullet machine-discoverable for downstream cross-file checks.
