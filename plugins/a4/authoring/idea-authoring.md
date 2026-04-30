# a4 — idea authoring

> **Audience:** Workspace authors writing `<project-root>/a4/**/*.md` files (or LLMs editing them on the user's behalf). Not for a4 plugin contributors — implementation references live in `../dev/`.

An idea at `a4/idea/<id>-<slug>.md` is a **pre-pipeline quick-capture slot** — a Jira-issue-style "Idea / Suggestion" with the minimum fields needed to participate in the issue family. Ideas are independent possibilities recorded raw; they may later graduate into a spec, use case, task, or spark brainstorm via the `promoted:` field.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`.

## Boundary with `review/`

- **idea** — independent possibility, captured raw; not bound to current progress.
- **review** — gap in current spec, bound to progress (something downstream depends on it).

If ignoring the input blocks or degrades current spec work, it is a review item; otherwise it is an idea. When in doubt, ideas are the safer slot — they have no `target:` and no cascade obligations.

## Frontmatter contract (do not deviate)

```yaml
---
type: idea
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | promoted | discarded
promoted: []          # populated when status → promoted (e.g., [usecase/5-search])
related: []           # soft links to other artifacts
labels: []            # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `idea` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable one-liner |
| `status` | yes | enum | `open` \| `promoted` \| `discarded` |
| `promoted` | no | list of paths | populated when `status → promoted` (e.g., `[usecase/5-search, spark/2026-04-24-1730-idea-x.brainstorm]`) |
| `related` | no | list of paths | soft links to other artifacts |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

- `id` is allocated by the id allocator (workspace-global, monotonic). Never invent or reuse an id.
- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `promoted:` lists the pipeline artifacts this idea graduated into (e.g., `[usecase/5-search, spark/2026-04-24-1730-idea-x.brainstorm]`). The list lives on the **idea** side; the target file does not carry a back-reference. Reverse views are derived on demand.
- `related:` is the soft-link slot for ideas tied to other artifacts that are not direct graduation targets.
- Path values are plain strings without `.md` and without brackets.
- Both `created` and `updated` are unquoted ISO dates. Bump `updated:` on every revision.

### Deliberately excluded fields

The idea family deliberately omits four fields that other issue families carry. These omissions are intentional, not oversight:

- `priority` — ideas are pre-prioritization; prioritization attaches to the graduation target (spec / usecase / task) at promote time.
- `source` — ideas are effectively always `self`; recording the source carries no information content.
- `target` — ideas are independent of other artifacts by definition; a `target` would blur the boundary with `review/`.
- `kind` — only one kind of idea (unlike `review/` which unifies finding / gap / question).

Do not re-introduce these fields without first updating this file and `./validator-rules.md`.

### Lifecycle and writer ownership

```
open      → discarded | promoted
promoted  → (terminal)
discarded → (terminal)
```

Per-status meaning:

- `open` — Captured but not yet graduated. Default initial status.
- `promoted` — Idea graduated into one or more pipeline artifacts named in `promoted:`. Terminal.
- `discarded` — Idea deliberately dropped (already covered, not aligned, no longer worth capturing). Terminal.

Writer rules (idea-specific):

- `open` is the **only** initial status. New ideas are always born at `open`.
- The idea family has **no cascade** — the PostToolUse cascade hook doesn't flip related files for it (the family is absent from `FAMILY_TRANSITIONS`). `status:` is hand-flipped after the user populates `promoted:` (or decides to discard).
- Drift between `status:` and `promoted:` is surfaced as a separate consistency check: non-empty `promoted:` while `status: open` is a mismatch (the idea has graduated but the status was not flipped); empty `promoted:` while `status: promoted` is the inverse mismatch.
- There is **no reverse path** from `promoted` or `discarded` — both are terminal. To revive a discarded idea, author a fresh idea (and reference the prior via `related:` if the lineage matters).

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

The idea body is **largely free**. Quick-capture ideas are typically empty or carry a short `## Notes` paragraph; longer ideas may add `## Why This Matters` to articulate the motivation. The frontmatter is the primary artifact; body content is supporting context.

**Required:** none.

**Optional, emit only when applicable:**

- `## Notes` — short prose paragraph capturing the substance of the idea. Default home for any text the idea carries.
- `## Why This Matters` — motivation paragraph for ideas worth surfacing rather than just noting.
- `## Change Logs` — append-only audit trail when the body is materially edited post-create (rare; usually the original capture is the final word).
- `## Log` — optional, hand-maintained status-transition narrative. See `./body-conventions.md#log`.

Unknown H2 headings are tolerated.

## Common mistakes

- **Required-field omission** (`type`, `id`, `title`, `status`, `created`, `updated`).
- **`status: promoted` with empty `promoted:` list** (or non-empty `promoted:` with `status: open`) — surfaced as a consistency check.
- **Adding `priority`, `source`, `target`, or `kind`** — these are deliberately excluded. Unknown fields are tolerated, but they should not appear here.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't

- **Don't author an idea when the input is a gap in current spec work.** That is a `kind: gap` review item with `target:` populated. Ideas are independent possibilities, not blockers.
- **Don't introduce a `target:` field.** Ideas are independent by definition; a `target:` would blur the boundary with `review/`.
- **Don't pre-populate `promoted:` at create time.** The list is filled when the idea actually graduates into a pipeline artifact.
- **Don't auto-flip `status:` based on `promoted:` content.** The user owns the flip; drift is reported separately but does not mutate files.
- **Don't pack long-form prose into the body.** Long write-ups belong in specs, use cases, or wiki pages. Ideas are quick-capture; if the content has grown, promote it.
