# Iterate Mechanics — Shared Procedure for Review-Item Walks

> **Audience:** a4 plugin contributors editing `plugins/a4/` itself. Workspace authors editing `<project-root>/a4/**/*.md` should read `../authoring/` instead.

Single source of truth for the **formal procedure** every iterate flow follows when walking review items: how to filter the backlog, how to present it, how to transition status, and how to record the wiki edit. The **actual work** that happens between status flips (what to inspect, what to fix, which impact rules to apply) is stage-specific.

**Mental model.** Treat each iterate mode as a stage-specific mailbox: filter the inbox to messages addressed to this stage, open the priority queue, mark a message in-progress when starting, archive (resolve / discard) when done. The mechanics here are the mailbox protocol.

Companion to:
- [`../authoring/body-conventions.md`](../authoring/body-conventions.md) — body heading form, `## Change Logs` and `## Log` rules, link form.
- [`../authoring/review-authoring.md`](../authoring/review-authoring.md) — review-item frontmatter contract and lifecycle.
- [`../authoring/frontmatter-universals.md`](../authoring/frontmatter-universals.md) — universal frontmatter rules including writer-owned fields.

## Scope

This document covers the **mechanics** shared across iterate flows:

1. Filter the review backlog to the items this stage owns.
2. Present the backlog as a selectable priority table.
3. Transition status via the writer at every step.
4. Record wiki edits as `## Change Logs` bullets.
5. Honor the never-hand-edit / never-renumber discipline.

Stage-specific **work** — the impact rules, drift checks, cycle counters, scope-handling, and re-runs that each iterate mode adds on top — sits outside this mechanics doc.

## 1. Filter the backlog

A review item belongs to a given iterate flow when any entry in its `target:` list names that stage's wiki page or issue type. Typical filter expressions per stage:

| Stage | Filter |
|---|---|
| usecase iterate | `target` contains any of `usecase/*`, `context`, `actors`, `nfr` |
| domain iterate | `target` contains `domain` |
| arch iterate | `target` contains `architecture` |
| roadmap iterate | `target` contains `roadmap` or `task/*` |
| run iterate | `target` contains `task/*` or `roadmap` (typically from prior cycle's test-runner) |

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

Order by `priority` (High → Medium → Low), then by `created:`.

If a stage detects **staleness signals** (e.g., domain page's `updated:` predates recent UC additions, arch page's `## Change Logs` misses recent UC files) and no review item exists yet, the stage may surface them as "likely review triggers" alongside the backlog.

## 3. Transition status

Edit `status:` directly on the review item file. The PostToolUse cascade hook (`../scripts/a4_hook.py`) detects the pre→post transition, refreshes `updated:`, and runs any cross-file cascade — never hand-edit `updated:`. The hook does **not** write into `## Log`; if you want a transition recorded in the body, append a bullet by hand. If the rationale is worth keeping in the review's `## Log`, write that *first*, then flip `status:` last so the file is consistent at any read point.

**Pick → in-progress** (when an item is selected for work): set `status: in-progress`.

**Resolve → resolved** (when the fix is applied): set `status: resolved`. If `target:` includes a UC that just flipped to `discarded`, the cascade hook will already have flipped this item to `discarded` first — surface that to the user instead of resolving.

**Discard → discarded** (when the item is no longer applicable): set `status: discarded`.

Illegal direct edits (jumps not in `FAMILY_TRANSITIONS`) are surfaced by the Stop hook safety net, not the cascade hook. The cascade hook silently skips illegal jumps so it never amplifies a malformed edit.

## 4. Record wiki edits

When resolving an item involves editing a wiki page (`context.md`, `actors.md`, `domain.md`, `nfr.md`, `architecture.md`, `roadmap.md`, `bootstrap.md`):

- Append a dated bullet to the page's `## Change Logs` section: `- YYYY-MM-DD — [review/<id>-<slug>](review/<id>-<slug>.md)`. Create the section if it does not yet exist.
- The wiki close guard warns at resolve-time when `target:` lists wiki basenames but the referenced page lacks a `## Change Logs` bullet pointing at the review item.

Full `## Change Logs` formatting rules: [`../authoring/body-conventions.md`](../authoring/body-conventions.md).

## 5. Discipline (always-hold rules)

- **Never hand-edit** `status:` / `updated:` on any file the writer owns. Frontmatter fields with managing scripts are listed in [`../authoring/frontmatter-universals.md §Status writers`](../authoring/frontmatter-universals.md). The optional `## Log` body section is hand-maintained — the writer does not touch it.
- **Never renumber** ids. Ids are globally monotonic; gaps are allowed.
- **Never delete** review item files. `discarded` is the writer-managed terminal state.
- **Confirm before overwriting** any previously confirmed UC, wiki, or task content. Iteration preserves prior work.
- **Preserve cross-references.** When renaming or splitting, update `depends_on:`, `related:`, `target:` (the list now subsumes the old `wiki_impact:` semantics) consistently across affected files (consistency checks pick this up).
