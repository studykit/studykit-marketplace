# a4 Body Conventions

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

Body-level rules for every file under the `a4/` workspace. Covers section heading form, blank-line discipline, link form, and the `## Change Logs` / `## Log` audit-trail conventions.

Frontmatter-side rules live in `frontmatter-universals.md` (universal contract: `type:`, ids, path-reference format, dates, status writers, structural relationship fields, title placeholders) and the `## Frontmatter` section of each `<type>-authoring.md` (per-type field tables).

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

Inside a section, content is opaque markdown. Section detection runs on column-0 H2 lines; fenced code blocks are not scanned.

### Blank-line discipline

Leave one blank line above each H2 (except the first) and between heading and content. This is convention, not enforced syntax.

## Link form (body)

Body cross-references use **standard markdown links** — `[text](relative/path.md)`. The `.md` extension is retained; renderers (GitHub, VSCode, any markdown viewer) navigate them.

| Form | Example |
|------|---------|
| Cross-file reference | `[usecase/3-share-summary](../usecase/3-share-summary.md)` |
| Section anchor on a wiki page | `[architecture#sessionservice](../architecture.md#sessionservice)` |
| Sibling-folder reference | `[research/42-grpc-streaming](../research/42-grpc-streaming.md)` (from `a4/spec/`) |
| External URL | `[the spec text](https://example.com/spec)` |

Section anchors use the renderer's standard slugification (`## Decision Log` → `#decision-log`).

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

Issue files (`usecase`, `task`, `bug`, `spike`, `research`, `umbrella`, `review`, `spec`) may carry a `## Log` section. Its purpose is **resume context** — what a future Claude Code session (or any reader picking the file up cold) cannot reconstruct from frontmatter, the file's required body sections, the project's commits, or linked review items. The section is the agreed home for that mid-flight knowledge so the file alone is enough to continue the work.

For an `umbrella/<id>-<slug>` file specifically, the `## Log` is the umbrella's **reason for existing** — the cross-cutting narrative that spans its children. Per `./umbrella-authoring.md`, children inline-cite the umbrella path in their own `## Log` entries when they depend on a decision recorded there.

Write entries for things like:

- The approach currently being attempted, when it isn't yet visible in `## Description` / `## Acceptance Criteria` / `## Specification`.
- Where the work is blocked and the suspected cause.
- Decisions that changed the original framing — what changed, why, and which upstream artifact (UC, spec, architecture section) still needs to be reconciled.
- Open questions awaiting user input, or constraints the user gave only in conversation.
- The next concrete step a fresh session should pick up.

Do **not** restate things a fresh reader can already see:

- Frontmatter values — `status:`, `cycle:`, `updated:`.
- Which files were modified — `git log` / `git diff` cover this.
- Review-item bodies — link the review item and stop there.
- Command history (test runs, builds, etc.) — that belongs in the session handoff, not in the file.

Format is the author's choice — short bullets, one fact per line, append-only. Date prefixes are optional; use them when several entries accrete on the same topic.

```markdown
## Log

- Approach: caching at the Service layer (not Repository) because the cache key needs `user-id` and the Repository has no user context.
- Blocked: cache-key shape disagreement between [usecase/3-search-history](usecase/3-search-history.md) Flow and [spec/12-cache-key](spec/12-cache-key.md). Awaiting user input.
- 2026-05-01 — Decided to follow spec/12. UC 3 Flow still needs to point at spec/12.
- Next: SearchServiceTest cache-invalidation case is unwritten; eviction-timing assertion strategy undecided.
```

### Inline cross-references for cross-cutting narrative

Some Log entries depend on a decision recorded *elsewhere* — most often in a parent issue's `## Log` (when several siblings share a cross-cutting decision the parent owns). When this happens, write the entry so a reader who opens this file alone can discover the next file to read: **inline-cite the path of the file that carries the source narrative inside the Log entry itself.**

Use the body-link form (`[text](relative/path.md)`) for inline citations.

```markdown
## Log

- Approach: follow the caching strategy decided in [umbrella/5-search](../umbrella/5-search.md) `## Log`. This child only diverges on test-fixture shape.
- Blocked: cache eviction timing — local to this task, not covered by the umbrella decision.
```

Without this inline citation, the parent's `## Log` is invisible to a session that started from the child file. Frontmatter `parent:` makes the parent *discoverable* (reverse children lookup); the inline citation makes the parent *necessary to read* — only when the entry actually depends on it. Entries that are self-contained (work local to this file) need no cross-reference.

The same rule applies whenever a Log entry leans on narrative recorded in any other a4 file (sibling, related issue, spec, UC). Inline-cite the path; do not rely on the reader inferring it from frontmatter alone.

The section is optional in the schema, but **strongly recommended whenever the file is mid-flight** (any `status:` other than `open` / `complete` / `discarded` / `superseded`). The session-handoff workflow prompts the writer to append to `## Log` before snapshotting the session, so session-only context lands in the file it belongs to. The PostToolUse cascade hook refreshes `updated:` and cascades related files but **does not write into `## Log`**; all entries are written by hand.

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

- `frontmatter-universals.md` — universal frontmatter rules (the universal `type:` field, ids, path references, dates, status writers, structural relationship fields, title placeholders).
- `<type>-authoring.md` — binding per-type authoring contracts (the source of truth for body shape and the per-type field table).
- the id allocator — id allocator; required before writing any new issue file.
- Body shape is documentation-only; nothing validates section presence at runtime.
