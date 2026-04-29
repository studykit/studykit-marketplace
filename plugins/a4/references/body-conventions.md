# a4 Body Conventions

Body-level rules for every file under the `a4/` workspace. Covers section tag form, blank-line discipline, link form, and the `<change-logs>` / `<log>` audit-trail conventions.

Frontmatter-side rules (path format inside YAML, required fields, enums, the universal `type:` field) live in `frontmatter-schema.md`. The two should be read together.

## Scope

Applies to every markdown file inside the `a4/` workspace. Each file declares `type:` in frontmatter matching the body root tag. The recommended body shape per `type:` is documented in the per-type authoring contracts under `plugins/a4/references/`; reference XSDs at `../scripts/body_schemas/<type>.xsd` mirror the same shape for human readers but are not consumed by any runtime validator.

## Section tag form

A body section is a column-0 `<tag>...</tag>` block.

```markdown
<situation>

A meeting just ended; absent teammates need the outcome.

</situation>
```

Rules:

- **Open and close lines on column 0**, each on its own line. `<tag>` and `</tag>` cannot be inline.
- **Tag names** match the regex `^[a-z][a-z0-9-]*$` — lowercase ASCII, kebab-case, starting with a letter.
- **No attributes, no self-closing.** `<tag attr="x">` and `<tag/>` are rejected by the convention.
- **No nesting of the same tag** within itself. Different declared tags do not nest either — every section sits at the body's top level.
- **Unknown tags are tolerated** (so authors can drop in `<benchmarks>` or any supplemental block), provided the tag name is well-formed and the section is otherwise valid.
- **Anything outside a section block** that is not whitespace is stray content. H1 (`# Title`) is forbidden in body — title belongs to frontmatter `title:`.

Inside a section, content is opaque markdown. Use H3+ headings (`###`, `####`) freely, paragraphs, lists, code fences, tables, blockquotes, PlantUML — anything CommonMark or its extensions support. Fenced code blocks are passed through verbatim.

### Blank-line discipline

Writers emit blank lines around tags so the file renders predictably:

```markdown
<flow>

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.

</flow>
```

The blank lines are convention rather than enforced syntax, but renderers depend on them — without them, the content immediately under `<flow>` may merge with the open tag for some markdown processors. Keep the blank-line frame consistent.

## Link form (body)

Body cross-references use **standard markdown links** — `[text](relative/path.md)`. The `.md` extension is retained; renderers (GitHub, VSCode, any markdown viewer) navigate them.

| Form | Example |
|------|---------|
| Cross-file reference | `[usecase/3-search-history](../usecase/3-search-history.md)` |
| Section anchor on a wiki page | `[architecture#sessionservice](../architecture.md#sessionservice)` |
| Sibling-folder reference | `[task/42-grpc-streaming](../task/research/42-grpc-streaming.md)` (from `a4/spec/`) |
| External URL | `[the spec text](https://example.com/spec)` |

Relative paths are computed from the file containing the link to the target. Use the appropriate number of `../` segments. Section anchors use the renderer's lowercase-with-hyphens slugification of the heading text.

Frontmatter paths are different — they stay plain strings (no brackets, no `.md`) per `frontmatter-schema.md`.

## `<change-logs>` audit trail

Every wiki page (and every issue file that supports it) carries a `<change-logs>` section once a substantive edit has happened. The section is optional in every authoring contract — only emit it once it has content.

Format:

```markdown
<change-logs>

- 2026-04-23 — [usecase/1-share-summary](usecase/1-share-summary.md)
- 2026-04-24 — [usecase/3-search-history](usecase/3-search-history.md)
- 2026-04-24 — [spec/8-caching-strategy](spec/8-caching-strategy.md)

</change-logs>
```

Rules:

- One bullet per material edit. Newest last (chronological order).
- Each bullet: `- YYYY-MM-DD — [<causing-issue>](<relative-path>.md)` with optional trailing prose if a one-line note adds context (`- 2026-04-24 — [spec/8](spec/8.md): renamed Session → Conversation`).
- The link points to the **causing issue** — a UC, task, spec, or architecture-section anchor. Never a review item; review items are the surface where the user *picks* an edit to apply, but the change-log records *why* a wiki page changed and that "why" is the underlying issue.
- Bullets are append-only. Do not reorder, edit, or remove old entries; corrections accrete as new entries.

## `<log>` (writer-owned)

Every issue file (`usecase`, `task`, `review`, `spec`) gets an optional `<log>` section that the status writer (`scripts/transition_status.py`) maintains. Never write into `<log>` directly except for the one documented post-hoc-`complete` task case (a single creation entry, see [`frontmatter-schema.md §Task / Initial status policy`](frontmatter-schema.md)).

Format (one bullet per transition, written by the writer):

```markdown
<log>

- 2026-04-24 — draft → active — committed to current shape
- 2026-04-26 — active → superseded — replaced by spec/12

</log>
```

Bullets are append-only. The writer rebuilds the block from existing bullets plus the new entry on every status change, with stable blank-line discipline.

## Wiki Update Protocol

Wiki pages have no lifecycle (no `status:` field). They are continuously updated as issues land, driven by **issue state changes** — create, status transition, resolve — not by time.

### When to update

Update a wiki page when an issue change affects its content:

- **New UC, actor, or concept** — the affected wiki page (typically `actors.md`, `domain.md`, `context.md`) needs a section entry.
- **UC refinement** — may change framing in `context.md` or a concept definition in `domain.md`.
- **Architectural decision or component revision** — updates `architecture.md` (and occasionally `domain.md` when terminology shifts).
- **Resolved review item whose `target:` list contains a wiki basename** — triggers the close guard below.

Skip: typo fixes, metadata-only tweaks, internal notes that don't change semantics.

### How to update

1. Edit the affected `<section>` content.
2. Append a dated bullet to the page's `<change-logs>` section: `- YYYY-MM-DD — [<causing-issue>](<relative-path>.md)`. Create the section if it does not yet exist.
3. Bump the wiki page's frontmatter `updated:` to today.

### Deferring the update

If the user chooses not to update the wiki page immediately, open a review item so the gap does not disappear:

1. Allocate an id via `../scripts/allocate_id.py`.
2. Write `a4/review/<id>-<slug>.md` with:
   - `type: review`
   - `kind: gap`
   - `status: open`
   - `source: self`
   - `target: [<causing-issue-path>, <affected wiki basenames>]`
3. The wiki close guard (at session close) and drift detection (between sessions) re-surface the unresolved impact.

### Close guard

Before a session ends, for each review item that transitioned to `status: resolved` whose `target:` list contains one or more wiki basenames, verify each referenced wiki page contains a `<change-logs>` bullet whose markdown link points at the review item itself. Warn + allow override when missing. The drift detector at `../scripts/drift_detector.py` re-surfaces violations between sessions.

## Bumping `updated:`

- **Wiki pages** — bump `updated:` to today on every substantive change (any edit that produces a `<change-logs>` bullet). Metadata-only tweaks (whitespace, comment fixes) do not bump.
- **Issue files** — bump `updated:` on every status transition (the writer does this) or body change that is not a typo fix.

## Cross-references

- `frontmatter-schema.md` — frontmatter field rules, the universal `type:` field, per-type body section enums.
- `../scripts/body_schemas/<type>.xsd` — reference XSDs documenting required vs optional sections per type (no runtime validator consumes them).
- `<type>-authoring.md` — binding per-type authoring contracts (the source of truth for body shape).
- `../scripts/allocate_id.py` — id allocator; required before writing any new issue file.
- `../scripts/drift_detector.py` — scans `target:` for wiki basenames to surface unresolved `<change-logs>` and close-guard violations.
- `../scripts/validate_frontmatter.py` — enforces the frontmatter side (path-reference format, required fields, enums).
