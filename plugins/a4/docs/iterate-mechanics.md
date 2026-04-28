# Iterate Mechanics — Shared Procedure for Review-Item Walks

Single source of truth for the **formal procedure** every iterate flow follows when walking review items: how to filter the backlog, how to present it, how to transition status, and how to record the wiki edit. The **actual work** that happens between status flips (what to inspect, what to fix, which impact rules to apply) is stage-specific.

**Mental model.** Treat each iterate mode as a stage-specific mailbox: filter the inbox to messages addressed to this stage, open the priority queue, mark a message in-progress when starting, archive (resolve / discard) when done. The mechanics here are the mailbox protocol.

Companion to:
- [`body-conventions.md`](./body-conventions.md) — body tag form, `<change-logs>` and `<log>` rules, link form.
- [`frontmatter-schema.md`](./frontmatter-schema.md) — review-item frontmatter contract.

## Scope

This document covers the **mechanics** shared across iterate flows:

1. Filter the review backlog to the items this stage owns.
2. Present the backlog as a selectable priority table.
3. Transition status via the writer at every step.
4. Record wiki edits as `<change-logs>` bullets.
5. Honor the never-hand-edit / never-renumber discipline.

Stage-specific **work** — the impact rules, drift checks, cycle counters, scope-handling, and re-runs that each iterate mode adds on top — sits outside this mechanics doc.

## 1. Filter the backlog

A review item belongs to a given iterate flow when its `target:` (or its `wiki_impact:`) names that stage's wiki page or issue type. Typical filter expressions per stage:

| Stage | Filter |
|---|---|
| usecase iterate | `target: usecase/*` OR `target: context` OR `target: actors` OR `target: nfr` OR same in `wiki_impact` |
| domain iterate | `target: domain` OR `domain` in `wiki_impact` |
| arch iterate | `target: architecture` OR `architecture` in `wiki_impact` |
| roadmap iterate | `target: roadmap` OR `target: task/*` OR same in `wiki_impact` |
| run iterate | `target: task/*` OR `target: roadmap` (typically from prior cycle's test-runner) |

Always restrict to `status: open` (and `in-progress` for resume cases). Exclude `resolved` and `discarded`.

## 2. Present the backlog

Show the filtered set as a priority-ordered table. Use this shape:

> **Open review items (target: <stage>):**
>
> | # | Id | Kind | Target | Summary | Priority |
> |---|----|------|--------|---------|----------|
> | 1 | 6  | gap | usecase/3 | Missing validation on empty input | High |
> | 2 | 9  | question | — | How should concurrency be handled? | Medium |
> | 3 | 12 | finding | usecase/7 | Implementation leak in Flow step 4 | Medium |
>
> Which items would you like to address?

Order by `priority` (High → Medium → Low), then by `created:`. Drift-detector items (`source: drift-detector`) with `priority: high` lead.

If a stage detects **staleness signals** (e.g., domain page's `updated:` predates recent UC additions, arch page's `<change-logs>` misses recent UC files) and no review item exists yet, the stage may surface them as "likely review triggers" alongside the backlog.

## 3. Transition status via the writer

Every status change goes through `transition_status.py`. Never hand-edit `status:`, `updated:`, or `<log>` on a review item.

**Pick → in-progress** (when an item is selected for work):

```bash
uv run "../scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "review/<id>-<slug>.md" --to in-progress \
  --reason "iterate: user picked for resolution"
```

**Resolve → resolved** (when the fix is applied):

```bash
uv run "../scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "review/<id>-<slug>.md" --to resolved \
  --reason "<short — what was fixed>"
```

**Discard → discarded** (when the item is no longer applicable):

```bash
uv run "../scripts/transition_status.py" \
  "$(git rev-parse --show-toplevel)/a4" \
  --file "review/<id>-<slug>.md" --to discarded \
  --reason "<short — why discarded>"
```

The writer writes `status:`, bumps `updated:`, and appends a `<log>` entry. Do not write any of those fields directly.

## 4. Record wiki edits

When resolving an item involves editing a wiki page (`context.md`, `actors.md`, `domain.md`, `nfr.md`, `architecture.md`, `roadmap.md`, `bootstrap.md`):

- Append a dated bullet to the page's `<change-logs>` section: `- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md)`. Create the section (per the page's XSD) if it does not yet exist.
- The wiki close guard warns at resolve-time when `wiki_impact:` is non-empty but the referenced page lacks a `<change-logs>` bullet pointing at the causing issue.

Full `<change-logs>` formatting rules: [`body-conventions.md`](./body-conventions.md).

## 5. Discipline (always-hold rules)

- **Never hand-edit** `status:` / `updated:` / `<log>` on any file the writer owns. Frontmatter fields with managing scripts are listed in [`frontmatter-schema.md`](./frontmatter-schema.md).
- **Never renumber** ids. Ids are globally monotonic; gaps are allowed.
- **Never delete** review item files. `discarded` is the writer-managed terminal state.
- **Confirm before overwriting** any previously confirmed UC, wiki, or task content. Iteration preserves prior work.
- **Preserve cross-references.** When renaming or splitting, update `depends_on:`, `related:`, `target:`, `wiki_impact:` consistently across affected files (validators check this).
