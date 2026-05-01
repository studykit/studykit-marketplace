# a4 Wiki Body Conventions

Body-level rules for wiki pages (`actors.md`, `architecture.md`, `bootstrap.md`, `context.md`, `domain.md`, `nfr.md`, `roadmap.md`). Wiki pages have no lifecycle (no `status:` field — see `./frontmatter-universals.md` § Wiki family); they are continuously updated as issues land. The `## Change Logs` audit trail and the Wiki Update Protocol below are how that continuous update is recorded.

Common body rules (heading form, link form, `updated:` bumping) live in `./body-conventions.md`.

## `## Change Logs` audit trail

Every wiki page carries a `## Change Logs` section once a substantive edit has happened. The section is optional in every authoring contract — only emit it once it has content.

Format:

```markdown
## Change Logs

- 2026-04-23 — [usecase/1-share-summary](usecase/1-share-summary.md)
- 2026-04-24 — [usecase/3-search-history](usecase/3-search-history.md)
- 2026-04-24 — [spec/8-caching-strategy](spec/8-caching-strategy.md)
```

Rules:

- One bullet per material edit. Newest last (chronological order).
- Each bullet: `- YYYY-MM-DD — [<causing-issue>](<relative-path>.md)` with optional trailing prose if a one-line note adds context (`- 2026-04-24 — [spec/8](spec/8.md): renamed Session → Conversation`).
- The link points to the **causing issue** — a UC, task, spec, or architecture-section anchor. Never a review item; review items are the surface where the user *picks* an edit to apply, but the change-log records *why* a wiki page changed and that "why" is the underlying issue.
- Bullets are append-only. Do not reorder, edit, or remove old entries; corrections accrete as new entries.

## Wiki Update Protocol

Wiki pages have no lifecycle. They are updated when an **issue state change** affects their content — create, status transition, resolve.

### When to update

Update a wiki page when an issue change affects its content:

- **New UC, actor, or concept** — the affected wiki page (typically `actors.md`, `domain.md`, `context.md`) needs a section entry.
- **UC refinement** — may change framing in `context.md` or a concept definition in `domain.md`.
- **Architectural decision or component revision** — updates `architecture.md` (and occasionally `domain.md` when terminology shifts).
- **Resolved review item whose `target:` list contains a wiki basename** — triggers the close guard below.

Skip: typo fixes, metadata-only tweaks, internal notes that don't change semantics.

### How to update

1. Edit the affected `## <Section>` content.
2. Append a dated bullet to the page's `## Change Logs` section: `- YYYY-MM-DD — [<causing-issue>](<relative-path>.md)`. Create the section if it does not yet exist.
3. Bump the wiki page's frontmatter `updated:` to today.

### Deferring the update

If the user chooses not to update the wiki page immediately, open a review item so the gap does not disappear:

1. Allocate an id via the id allocator.
2. Write `a4/review/<id>-<slug>.md` with:
   - `type: review`
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: [<causing-issue-path>, <affected wiki basenames>]`
3. The wiki close guard (at session close) and drift detection (between sessions) re-surface the unresolved impact.

### Close guard

When a review item transitions to `status: resolved` and its `target:` list contains one or more wiki basenames, each referenced wiki page should contain a `## Change Logs` bullet whose markdown link points at the review item itself. This is an authoring invariant; nothing automated currently catches the omission, so the author is the only line of defense. Run `uv run ../scripts/validate.py <a4-dir>` after wiki edits if you want a sweep.

## Cross-references

- `./body-conventions.md` — common body rules (heading form, link form, `updated:` bumping).
- `./frontmatter-universals.md` — universal frontmatter rules (wiki frontmatter shape lives in § Wiki family).
- `./<type>-authoring.md` — per-type authoring contracts for individual wiki pages.
