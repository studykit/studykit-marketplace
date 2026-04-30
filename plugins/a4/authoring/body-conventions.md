# a4 Body Conventions

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

Body-level rules for every file under the `a4/` workspace. Covers section heading form, blank-line discipline, link form, and the `## Change Logs` / `## Log` audit-trail conventions.

Frontmatter-side rules live in `frontmatter-universals.md` (universal contract: `type:`, ids, path-reference format, dates, status writers, structural relationship fields), `validator-rules.md` (enforcement and cross-file consistency), and the `## Frontmatter` section of each `<type>-authoring.md` (per-type field tables).

## Scope

Applies to every markdown file inside the `a4/` workspace. Each file declares `type:` in frontmatter; the recommended body shape per `type:` is documented in the per-type authoring contracts under `plugins/a4/authoring/`. The binding form in the file body is the markdown heading defined below.

## Section heading form

A body section is an **H2 markdown heading** in Title Case with spaces, followed by free-form markdown content until the next H2 (or end of file).

```markdown
## Situation

A meeting just ended; absent teammates need the outcome.

## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.
```

Rules:

- **Section boundary is `## Heading`** — column-0 H2, on its own line. The section ends at the next column-0 H2 or end of file.
- **Heading text is Title Case** — each word capitalised, words separated by single spaces. Examples: `## Context`, `## Specification`, `## Change Logs`, `## Decision Log`, `## Open Questions`, `## Rejected Alternatives`, `## Acceptance Criteria`, `## Why This Matters`. Map the kebab-case slug from the per-type authoring contract to Title Case by replacing hyphens with spaces and capitalising each word.
- **No H1 in the body.** Title belongs to frontmatter `title:`. (Use of H1 is reserved; do not author one.)
- **Use H3+ for inner structure.** Inside a section, paragraphs, lists, code fences, tables, blockquotes, and `###`/`####`/… subheadings are all permitted. Section boundaries only fire on H2.
- **Sections do not nest.** Every declared section sits at the body's top level; you cannot place a recognised section inside another.
- **Unknown H2 headings are tolerated.** Authors may add supplemental sections (`## Benchmarks`, `## Migration Notes`, …) provided the heading is well-formed Title Case.
- **No stray content above the first section.** Anything in the body that is not whitespace must live under an H2 heading.

Inside a section, content is opaque markdown. Fenced code blocks are passed through verbatim — section detection only inspects the first character of column-0 H2 lines, and lines inside a fenced block (` ``` ` or `~~~`) are not treated as section boundaries.

### Blank-line discipline

Writers leave one blank line above each H2 (except the very first heading in the body) and one blank line between heading and content for predictable rendering:

```markdown
## Flow

1. Open the meeting record.
2. Click "share summary".
3. Confirm the channel.

## Validation
```

The blank lines are convention rather than enforced syntax, but renderers depend on them — without a blank line between an H2 and the content beneath, some processors merge the heading line into the following paragraph.

## Link form (body)

Body cross-references use **standard markdown links** — `[text](relative/path.md)`. The `.md` extension is retained; renderers (GitHub, VSCode, any markdown viewer) navigate them.

| Form | Example |
|------|---------|
| Cross-file reference | `[usecase/3-share-summary](../usecase/3-share-summary.md)` |
| Section anchor on a wiki page | `[architecture#sessionservice](../architecture.md#sessionservice)` |
| Sibling-folder reference | `[research/42-grpc-streaming](../research/42-grpc-streaming.md)` (from `a4/spec/`) |
| External URL | `[the spec text](https://example.com/spec)` |

Relative paths are computed from the file containing the link to the target. Use the appropriate number of `../` segments. Section anchors use the renderer's lowercase-with-hyphens slugification of the heading text (so `## Decision Log` resolves to `#decision-log`).

Plain `#<id>` text (e.g., `see #42 for the rollout plan`) is also acceptable in prose. It renders as plain text in local markdown viewers but is auto-linked as a cross-issue reference in GitHub Issues / Pull Requests when an `a4/` workspace is mirrored into a tracker. Use it for shorthand mentions; use the markdown-link form when local navigation matters.

Frontmatter paths are different — they stay plain strings (no brackets, no `.md`) per `frontmatter-universals.md §Path references`.

## `## Change Logs` audit trail

Every wiki page (and every issue file that supports it) carries a `## Change Logs` section once a substantive edit has happened. The section is optional in every authoring contract — only emit it once it has content.

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

## `## Log`

Issue files (`usecase`, `task`, `review`, `spec`) may carry an optional `## Log` section as a manual audit trail of status transitions or other notable edits. Format is the author's choice — a common shape is one bullet per transition:

```markdown
## Log

- 2026-04-24 — draft → active — committed to current shape
- 2026-04-26 — active → superseded — replaced by spec/12
```

The PostToolUse cascade hook refreshes `updated:` on the primary edit and flips related files, but **does not write into `## Log`**. If you want a transition recorded in the body, append the bullet by hand. The section is optional and may be omitted entirely.

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

When a review item transitions to `status: resolved` and its `target:` list contains one or more wiki basenames, each referenced wiki page should contain a `## Change Logs` bullet whose markdown link points at the review item itself. This is an authoring invariant rather than an enforced check at the moment — there is no automated guard or cross-session re-surfacer. Run the validator (`../scripts/validate.py`) after wiki edits if you need a sweep, and consider extending the validator with a new check if the gap matters.

## Bumping `updated:`

- **Wiki pages** — bump `updated:` to today on every substantive change (any edit that produces a `## Change Logs` bullet). Metadata-only tweaks (whitespace, comment fixes) do not bump.
- **Issue files** — bump `updated:` on every status transition (the writer does this) or body change that is not a typo fix.

## Cross-references

- `frontmatter-universals.md` — universal frontmatter rules (the universal `type:` field, ids, path references, dates, status writers, structural relationship fields).
- `validator-rules.md` — schema enforcement and cross-file status consistency tables.
- `<type>-authoring.md` — binding per-type authoring contracts (the source of truth for body shape and the per-type field table).
- the id allocator — id allocator; required before writing any new issue file.
- Body shape is documentation-only; nothing validates section presence at runtime.
