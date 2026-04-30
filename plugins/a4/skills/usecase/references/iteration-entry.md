# Iteration Entry Procedure (usecase)

usecase-specific addendum on top of the shared procedure in [`plugins/a4/dev/iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/dev/iterate-mechanics.md). This document describes only what the **usecase** iterate flow does between writer calls — research-reflected check, revising-UC scope handling, allowed activities, work-surface summary.

When entering Iteration mode (an existing `a4/` workspace with UC files is found), the goal is to surface unresolved review items, unreflected research/exploration reports, and any wiki drift so the session picks up coherently.

## 1. Scan the workspace

List the current state. Do **not** read every UC up front — read on demand.

- Wiki pages present: `a4/{context,actors,domain,nfr}.md` (each optional except `context.md`).
- UC count: `ls a4/usecase/*.md | wc -l`.
- Open review items: `grep -l 'status: open' a4/review/*.md` (if any).
- Research reports: `ls a4/research/*.md` (if the folder exists).

## 2. Backlog (per the mechanics)

Filter open review items to this stage's mailbox: items whose `target:` list contains any of `usecase/*`, `context`, `actors`, `nfr`. Present as the priority backlog per [`iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/dev/iterate-mechanics.md) §1–§2. The writer-call protocol for **pick → in-progress** and **resolve → resolved** is in §3 of that document.

### Revising-UC priority

If the iterate session is scoped to a specific UC (e.g., the user said "fix UC-5" and UC-5 is `status: implementing` / `revising`), first present review items where `target: usecase/<that-uc>` and `source: task-implementer` (these describe the blocking ambiguity) before the general backlog. When editing begins, flip the UC's `status:` to `revising` by editing the frontmatter directly. The PostToolUse cascade hook detects `implementing → revising`, refreshes `updated:` on the UC, and resets `progress` / `failing` tasks (across `task` / `bug` / `spike` / `research`) back to `pending`. At session end, Step 6 ready-gate flips `revising → ready`.

## 3. Unreflected research / exploration reports

Check `a4/research/` for reports that were written but never reflected into UCs. A report is unreflected when no UC cites it in body prose and no review item references it. Present these to the user and decide whether to reflect.

## 4. Work-surface summary

Present a brief status:

- UCs confirmed: `<count>`, of which `shipped`: `<count>`, `implementing`: `<count>`, `revising`: `<count>`, `blocked`: `<count>`, `discarded`: `<count>`
- Actors in `actors.md`: `<count>` (if the file exists)
- Domain concepts in `domain.md`: `<count>` (if the file exists)
- Open review items: `<count>` (listed above)
- Research reports pending review: `<count>`

## 5. Activities the user can pick

- **Resolve review items** — pick from the backlog; for each, read the target UC and wiki pages and walk through the resolution.
- **Add new use cases** — resume the Discovery Loop. Each new UC gets a fresh id from the allocator.
- **Refine actors** — edit `actors.md`; add footnote markers for changes.
- **Split oversized UCs** — allocate new ids per child, write new UC files, adjust `related` (and `## Dependencies` body links) in other UCs that referenced the parent.
- **Extend the domain model** — handed off to `/a4:domain` (cross-cutting concept extraction is its own skill, not part of usecase).
- **Re-analyze relationships** — update `related` / `labels` across UC files; cross-UC ordering goes into the `## Dependencies` body section.

## Usecase-specific iteration rules

Most discipline is shared (see [`iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/dev/iterate-mechanics.md) §5). usecase adds:

- **Show before/after on UC modifications** — when modifying an existing UC body, present the before/after to the user before writing.
- **Preserve allocator gaps** — when adding new UCs after iteration, gaps from earlier discards/renumbers stay; do not compact ids.
- **Wiki edits inside iterate** still flow through `## Change Logs` per the shared rules; no usecase-specific override.
