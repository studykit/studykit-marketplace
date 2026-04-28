# a4 — context wiki authoring

`a4/context.md` is the **upstream framing wiki**. It records the original idea, the problem framing the workspace is shaped around, and (optionally) the screen-navigation narrative that ties UI use cases together. Every other wiki page and every issue family indirectly assumes the framing this page captures.

Companion to [`./frontmatter-schema.md §Wiki pages`](./frontmatter-schema.md), `./body-conventions.md`, `./wiki-authorship.md`.

## How to author — always via `/a4:usecase`

Do **not** hand-craft `context.md` with `Write`. Always invoke `/a4:usecase` so the original idea is captured verbatim, the problem framing is shaped through Socratic interview, and any screen-grouping narrative is co-authored with the UCs that participate.

The skill creates `context.md` in Step 1 ("Receive the Idea") of a new workspace, and revises it via the in-situ wiki nudge whenever a UC change broadens or refines the framing.

If you must read the file to answer a question, prefer `extract_section.py a4/context.md <tag>` over loading the whole markdown.

## Authorship — who can edit this page

Per `./wiki-authorship.md`:

- **`/a4:usecase` is the primary author.** It owns all body sections. In-situ edits from `/a4:usecase` are unrestricted.
- **No other skill edits in-situ.** When another stage discovers a framing issue, it emits a review item with `target: context` and `wiki_impact: [context]`.

If you find yourself wanting to edit `context.md` from any context other than `/a4:usecase`, **stop** and emit the review item instead.

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

**Required (enforced by `../scripts/body_schemas/context.xsd`):**

- `<original-idea>` — the user's input, captured **verbatim** at workspace creation. Do not paraphrase. Subsequent edits append follow-up clarifications as new paragraphs; the original quote stays.
- `<problem-framing>` — the shape the team commits to working on: who has the problem, what current solution is failing, what success looks like at a coarse level. Refined progressively through Socratic interview.

**Optional, emit only when applicable:**

- `<screens>` — for projects with UI use cases, the screen-navigation narrative grouping UCs into screens. Each screen block lists the screen slug (also added to UC `labels:`) and the UCs that participate, with markdown links. Skip for headless, non-UI, or single-screen projects.
- `<change-logs>` — append-only audit trail of why this page was edited (dated bullets with markdown links to the causing UC, review item, or spec).

Unknown kebab-case tags are tolerated by the XSD's openContent.

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

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
- **Required section missing** (`<original-idea>`, `<problem-framing>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`.
- **Same-tag nesting** → `body-tag-invalid`.
- **H1 in body** → `body-stray-content`. Page name is the file basename.
- **`type:` mismatch** with filename → frontmatter validator error.

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file context.md
```

## Don't

- **Don't edit from any skill other than `/a4:usecase`.** Emit a review item with `target: context`.
- **Don't paraphrase `<original-idea>`.** It is the verbatim user input. Edits append; the original block stays.
- **Don't write detailed UC flows here.** Use cases live in `a4/usecase/<id>-<slug>.md`. `context.md` carries framing only.
- **Don't put domain concepts here.** Cross-cutting concepts belong in `domain.md`'s `<concepts>` section.
- **Don't write actor rosters here.** Actor definitions belong in `actors.md`'s `<roster>` section.
- **Don't pack screen mockups inline.** HTML mocks live under `a4/mock/<screen-slug>/`; reference them from `<screens>` if useful.
- **Don't append `<change-logs>` bullets without a markdown link.** The link is what powers the close-guard / drift checks.

## After authoring

`/a4:usecase` does not commit; the file is left in the working tree. Subsequent `/a4:usecase` invocations refine `<problem-framing>` and optionally seed `<screens>` once UI UCs settle.
