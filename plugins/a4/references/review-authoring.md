# a4 — review authoring

A review item at `a4/review/<id>-<slug>.md` is the **unified conduit for findings, gaps, and questions** discovered while working in the a4 workspace. The single `kind:` field discriminates them; lifecycle is identical across kinds:

- `finding` — something is wrong / inconsistent in an existing artifact (bad UC abstraction, contract mismatch, drift between files).
- `gap` — something is missing that ought to exist (a UC that no spec covers, an architectural choice nobody recorded, a wiki page that has not been updated to reflect a confirmed change).
- `question` — an open question the conversation could not resolve in place (deferred decision, unclear constraint).

Review items are **never the user's primary product** — they are the deferred-work mailbox between stages. They are emitted by reviewer agents, by `../scripts/drift_detector.py` (`source: drift-detector`), and by single-edit defer paths (`source: self`).

Companion to [`./frontmatter-schema.md §Review item`](./frontmatter-schema.md), `./body-conventions.md`.

## Reading a review item

If only a specific section is needed to answer a question, prefer `extract_section.py <file> <tag>` over loading the whole file.

## Frontmatter contract (do not deviate)

```yaml
---
type: review
id: <int — globally monotonic across the workspace>
kind: finding | gap | question
status: open | in-progress | resolved | discarded
target: <path>            # what this review is about; omit for cross-cutting
source: self | drift-detector | <reviewer-agent-name>
wiki_impact: []           # list of wiki basenames needing update on resolve
priority: high | medium | low
labels: []                # free-form; drift uses drift:<kind>, drift-cause:<slug>
milestone: <optional>
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `id` is allocated by `../scripts/allocate_id.py` (workspace-global, monotonic). Never invent or reuse an id.
- `kind` is **required** — `finding`, `gap`, or `question`. The three share lifecycle but signal different content shapes:
  - `finding` body explains what is wrong and where.
  - `gap` body explains what is missing and why it should exist.
  - `question` body states the open question and what would resolve it.
- `target:` points at the artifact this review is about. Accepts any issue path (`usecase/<id>-<slug>`, `task/<id>-<slug>`, `spec/<id>-<slug>`) or a wiki basename (`architecture`, `domain`, `context`, `actors`, `nfr`, `roadmap`, `bootstrap`). **Omit `target:` entirely when the concern is cross-cutting** — do not invent a placeholder.
- `source:` records who emitted the item. The validator currently accepts any string, but the conventional set is `self`, `drift-detector`, and reviewer-agent names. Do not invent new values without updating `./frontmatter-schema.md`.
- `wiki_impact:` lists **wiki basenames** (no `.md`, no folder prefix) whose `<change-logs>` must record the resolution. Used by the close guard at resolve-time. Empty list when no wiki page is affected.
- `priority:` drives ordering in iterate backlog presentation (High → Medium → Low). Drift items at `priority: high` lead.
- `labels:` are free-form. The drift detector reserves `drift`, `drift:<kind>`, and `drift-cause:<slug>` for dedup; do not reuse these prefixes for unrelated tags.
- Path values are plain strings without `.md` and without brackets (e.g., `usecase/3-search-history`, not `[usecase/3-search-history.md]`).
- Both `created` and `updated` are unquoted ISO dates. Bump `updated:` on every revision; the writer bumps it on status flips.

### Cascade — `target: usecase/X` discarded chain

When a UC at `target:` flips to `discarded`, **every open review item** with that `target:` automatically cascades to `discarded` via `../scripts/transition_status.py`. Do not flip these by hand. The cascade does not apply to `target: <wiki>` (wiki pages have no `discarded` state) or `target: task/...` (task discards are independent).

### Lifecycle and writer ownership

```
open        → discarded | in-progress
in-progress → discarded | resolved
resolved    → (terminal)
discarded   → (terminal)
```

Per-status meaning:

- `open` — Item is in the inbox. Default initial status. Picked up by the iterate flow whose filter matches `target:` / `wiki_impact:`.
- `in-progress` — Item selected from the iterate backlog. Active resolution.
- `resolved` — Fix landed. The artifact named in `target:` (and any wiki page in `wiki_impact:`) reflects the resolution. Terminal.
- `discarded` — No longer applicable (e.g., the underlying UC was discarded, the finding was re-evaluated as not-a-bug, the question was overtaken by events). Terminal.

Writer rules:

- `open` is the **only** initial status. New items are always born at `open`; everything else is a transition.
- All status changes after the initial create flow through `../scripts/transition_status.py`. Never write `status:` directly post-create.
- `open → in-progress` is the iterate-flow's "user picked this item" flip; `in-progress → resolved` (or `→ discarded`) closes it.
- `open → discarded` is allowed for items that are dismissed without being picked (e.g., obvious duplicate, inapplicable on second look).
- The drift detector **dedups** against open / in-progress / discarded items with matching `(kind, target, drift-cause:<slug>)` fingerprints — discarded counts as a tombstone so the same drift does not re-emit. Resolved items do not block re-emission (the drift returned).

### Close guard — `wiki_impact:` must be honored on resolve

A review item with **non-empty `wiki_impact:`** cannot cleanly transition to `resolved` unless each referenced wiki page records the change in its `<change-logs>` section with a markdown link to the causing issue (the review's `target:`, when present, or the review item itself). Enforcement is a **warning with override** — `transition_status.py` proceeds, but the drift detector re-surfaces violations as fresh `close-guard` review items.

When resolving, append the bullet to each affected wiki:

```markdown
<change-logs>

- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md) — <short note>

</change-logs>
```

Create the `<change-logs>` section if it does not yet exist (per the page's XSD).

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks (lowercase + kebab-case), with markdown content between the open and close lines. H1 (`# Title`) is forbidden in the body. Use H3+ headings inside sections freely.

Review item bodies are **deliberately minimal** — they hold a single observation, not a long-form artifact.

**Required (enforced by `../scripts/body_schemas/review.xsd`):**

- `<description>` — what the finding / gap / question is, why it matters, and (when relevant) how to resolve. Concise. The body of a review item is a hand-off note, not an essay.

**Optional, emit only when applicable:**

- `<change-logs>` — append-only audit trail when the review item body is materially edited post-create (rare; usually the original description is the final word).
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent; the first status flip writes the first entry. **Never write into `<log>` directly.**

Unknown kebab-case tags are tolerated by the XSD's openContent — useful for embedding `<diff>`, `<repro>`, or `<context>` blocks when the description benefits from structured supplemental content. Use sparingly; a one-paragraph `<description>` is usually enough.

There is no standalone "title" body section — the file's frontmatter carries no `title:` field either. The slug + first line of `<description>` serves as the human-readable name in iterate backlogs.

### Body-link form

Body cross-references are standard markdown links — `[text](relative/path.md)` — with the `.md` extension retained (e.g., `[usecase/3-search-history](../usecase/3-search-history.md)`). Frontmatter list paths are different (plain strings, no `.md`).

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`. Anything in the body that is not whitespace must live inside a `<tag>...</tag>` block.
- **`<description>` missing** → `body-xsd`. The only required body section.
- **Inline or attribute-bearing tags** → `body-tag-invalid`. Open and close lines must be on column 0; no attributes; no self-closing.
- **Same-tag nesting** → `body-tag-invalid`. Sections do not nest; every section sits at the body's top level.
- **H1 in body** → `body-stray-content`.
- **`wiki_impact:` entry not in the wiki-type enum** → frontmatter validator error. Use bare basenames (`architecture`, not `architecture.md`, not `a4/architecture`).

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file review/<id>-<slug>.md
```

## Don't

- **Don't hand-edit `status:`.** Use `transition_status.py` (typically via the iterate flow that owns the item's `target:`).
- **Don't hand-edit `<log>`.** Writer-owned. Every entry comes from `transition_status.py`.
- **Don't delete a review item file.** `discarded` is the writer-managed terminal state. Deleting orphans the cascade bookkeeping and breaks drift dedup.
- **Don't invent placeholder `target:` values.** When the concern is cross-cutting, omit `target:` entirely.
- **Don't hand-flip the discarded cascade.** When a UC flips to `discarded`, the writer cascades open review items pointing at it.
- **Don't reuse `drift`, `drift:<kind>`, `drift-cause:<slug>` labels** for non-drift items. Those prefixes are reserved for the drift detector's dedup fingerprint.
- **Don't pack multiple findings / gaps / questions into one review item.** Re-emit one per concern; iterate flows process items individually.
- **Don't mark `resolved` when the wiki edit was deferred.** Open a fresh follow-up review item targeting the wiki, leave this item `in-progress` (or close as `discarded` with rationale).
- **Don't override the close guard silently.** The drift detector will re-surface the violation; better to fix the wiki edit now.
- **Don't author review items as long-form prose.** Bodies are hand-off notes. Long write-ups belong in specs, UCs, or wiki pages.
