# a4 Obsidian Markdown Conventions

Body-level markdown conventions for every file written by an a4 skill. Covers wikilink / embed syntax, the footnote audit trail, and the wiki update protocol.

Frontmatter-side rules (path format inside YAML, required fields, enums) live in [frontmatter-schema.md](./frontmatter-schema.md). This document is the body-side counterpart — the two should be read together.

## Scope

Applies to files written into the `a4/` workspace:

- **Wiki pages** — `context.md`, `actors.md`, `domain.md`, `nfr.md`, `architecture.md`, `plan.md`, `bootstrap.md`. Continuously updated. Follow the Wiki Update Protocol below.
- **Issue bodies** — `usecase/*.md`, `task/*.md`, `review/*.md`, `decision/*.md`, `idea/*.md`. Use wikilinks for body cross-references; the update protocol applies only to wiki pages, not to issue bodies.
- **Spark files** — `spark/*.brainstorm.md`. Use wikilinks in body prose. Spark files are append-only session artifacts and do **not** follow the wiki update protocol. (Historical note: `spark/*.decide.md` was retired; decisions now live at `a4/decision/<id>-<slug>.md`, recorded by `/a4:decision` after a conversational convergence, with supporting research produced by `/a4:research` at project-root `./research/<slug>.md` and cited from the decision's body as `[[research/<slug>]]` wikilinks.)

## Link syntax (body)

In body prose, use Obsidian wikilinks and embeds. These are the canonical forms:

| Form | Rendered as | Use for |
|------|-------------|---------|
| `[[usecase/3-search-history]]` | Reference link (Obsidian surfaces it as a backlink on the target) | Cross-references in body prose |
| `[[architecture#SessionService]]` | Reference to a specific heading | Pointing at a wiki page section |
| `![[usecase/3-search-history]]` | Embed (Obsidian inlines the full target file) | Pulling a UC into a context page or a review item |
| `![[usecase/3-search-history#Flow]]` | Embed of a specific heading section | Showing only one section |

Aliases — `[[path\|display text]]` — work when the default basename reads poorly. Use sparingly; plain wikilinks read cleaner in diffs.

**Frontmatter paths are different.** Frontmatter fields (`depends_on`, `implements`, `target`, etc.) use plain strings with no brackets and no `.md` suffix, per [frontmatter-schema.md](./frontmatter-schema.md). Do not mix the two forms:

| Context | Example |
|---------|---------|
| Body prose | `[[usecase/3-search-history]]` |
| Frontmatter | `depends_on: [usecase/3-search-history]` |

## Footnote audit trail

Wiki pages record the cause of each material update as a footnote whose payload wikilinks the causing issue.

### Inline marker

Append `[^N]` to the sentence or heading that changed. `N` is file-local — starts at `1` per wiki page, monotonically increases. The same marker label may appear multiple times in the body if several paragraphs changed in the same update.

### `## Changes` section

A single `## Changes` section at the bottom of the wiki page resolves every marker. One line per marker, newest last:

```markdown
## Changes

[^1]: 2026-04-23 — [[usecase/1-share-summary]]
[^2]: 2026-04-24 — [[usecase/3-search-history]]
[^3]: 2026-04-24 — [[decision/8-caching-strategy]]
```

Format: `[^N]: YYYY-MM-DD — [[causing-issue]]`

- **Date** — today in `YYYY-MM-DD`.
- **Wikilink target** — the **causing issue**: a UC, task, decision, or architecture-section heading (e.g., `[[architecture#SessionService]]`). Never a review item; review items surface in the close guard but are not what the wiki records as "why this section changed."

### Full example

```markdown
## Actors

Meeting Organizer[^2] — drives the share-summary flow; initiates UC-3.

## Changes

[^1]: 2026-04-23 — [[usecase/1-share-summary]]
[^2]: 2026-04-24 — [[usecase/3-search-history]]
```

## Wiki Update Protocol

Wiki pages have no lifecycle (no `status:` field). They are continuously updated as issues land, driven by **issue state changes** — create, status transition, resolve — not by time.

### When to update

Update a wiki page when an issue change affects its content:

- **New UC, actor, or concept** — the affected wiki page (typically `actors.md`, `domain.md`, `context.md`) needs a section entry.
- **UC refinement** — may change framing in `context.md` or a concept definition in `domain.md`.
- **Architectural decision or component revision** — updates `architecture.md` (and occasionally `domain.md` when terminology shifts).
- **Resolved review item with non-empty `wiki_impact:`** — triggers the close guard below.

Skip: typo fixes, metadata-only tweaks, internal notes that don't change semantics.

### How to update

1. Edit the affected section(s) of the wiki page.
2. Append an inline `[^N]` footnote marker in each modified section.
3. Append a `## Changes` entry: `[^N]: YYYY-MM-DD — [[causing-issue]]`.
4. Bump the wiki page's frontmatter `updated:` to today.

### Deferring the update

If the user chooses not to update the wiki page immediately, open a review item so the gap does not disappear:

1. Allocate an id via `${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py`.
2. Write `a4/review/<id>-<slug>.md` with:
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: <causing-issue-path>`
   - `wiki_impact: [<affected wiki basenames>]`
3. The wiki close guard (at session close) and drift detection (between sessions) re-surface the unresolved impact.

### Close guard

Before a session ends, for each review item that transitioned to `status: resolved` with non-empty `wiki_impact`, verify each referenced wiki page contains a footnote whose `## Changes` payload wikilinks the causing issue. Warn + allow override when missing. The drift detector at `plugins/a4/scripts/drift_detector.py` re-surfaces violations between sessions.

## Bumping `updated:`

- **Wiki pages** — bump `updated:` to today on every substantive change (any edit that produces a footnote marker). Metadata-only tweaks (whitespace, comment fixes) do not bump.
- **Issue files** — bump `updated:` on every status transition or body change that is not a typo fix.

## Cross-references

- [frontmatter-schema.md](./frontmatter-schema.md) — frontmatter field rules (required fields, enums, frontmatter-path format).
- [obsidian-dataview.md](./obsidian-dataview.md) — dataview query patterns for the INDEX.md blocks and reverse-derived relationship views.
- `plugins/a4/scripts/allocate_id.py` — id allocator; required before writing any new issue file.
- `plugins/a4/scripts/drift_detector.py` — reads `wiki_impact` to surface unresolved footnote + close-guard violations.
- `plugins/a4/scripts/validate_frontmatter.py` — enforces the frontmatter-side of path references.
- `plugins/a4/scripts/validate_body.py` — enforces the body-side rules on this page: footnote definition format, label monotonicity, payload-not-a-review-item, and body-wikilink resolution.
- `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` — ADR, the authoritative rationale source.
