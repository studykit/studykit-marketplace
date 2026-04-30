# a4 — usecase authoring

A use case at `a4/usecase/<id>-<slug>.md` is a **concrete description of how a user (actor) interacts with the system** to achieve a goal in a specific situation, with a defined flow and an expected outcome. Use cases are the user-facing scope unit — they sit upstream of tasks (which deliver them) and downstream of `context.md` (which frames the problem). They hand off to implementation when their `## Flow` / `## Validation` / `## Error Handling` close enough to drive AC for tasks.

Companion to [`./frontmatter-universals.md`](./frontmatter-universals.md), `./body-conventions.md`.

## Abstraction discipline

Use cases stay at the **user level** — what the actor does, not what the system does internally. A UC that says "the system stores the record in PostgreSQL" is wrong shape; "the user submits the form and sees a confirmation" is right. Internal mechanics belong to `architecture.md` and tasks.

## Frontmatter contract (do not deviate)

```yaml
---
type: usecase
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: draft | ready | implementing | revising | shipped | superseded | discarded | blocked
actors: [<slug>, ...]    # actor slugs as defined in actors.md
supersedes: []           # list of paths to prior UCs this one replaces
related: []              # catchall for cross-references
labels: []               # free-form tags (incl. group slugs like screen-dashboard)
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `usecase` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `draft` \| `ready` \| `implementing` \| `revising` \| `shipped` \| `superseded` \| `discarded` \| `blocked` |
| `actors` | no | list of strings | actor names as defined in `actors.md` |
| `supersedes` | no | list of paths | prior use cases this UC replaces |
| `related` | no | list of paths | catchall |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `actors:` lists slug identifiers defined as rows in `actors.md`'s `## Roster` section (e.g., `meeting-organizer`, `team-member`, `platform`). New actors flow through `actors.md` first; UC frontmatter references them by slug. Platform-capability UCs typically use `actors: [platform]` or another suitable system actor.
- UC-to-UC ordering is **not** carried in frontmatter (a4 v6.0.0). Implementation ordering belongs to tasks via `task.depends_on:`; soft narrative dependencies between UCs go in `## Dependencies` body prose with markdown links.
- UC-to-spec ties are **not** carried in frontmatter (a4 v6.0.0). When a spec governs the UC, cite it from `## Situation` / `## Validation` / `## Error Handling` / `## Dependencies` body prose via markdown link (`[spec/<id>-<slug>](../spec/<id>-<slug>.md)`); add the spec to `related:` only when it is a soft cross-reference worth indexing in frontmatter searches.
- `supersedes:` lists prior UC paths this one replaces. The writer cascades `shipped → superseded` on the listed targets when this UC reaches `shipped`. Do not hand-flip the predecessor's status.
- The reverse view of `task.implements:` (which tasks deliver this UC) is computed on demand by `search.py` and roadmap surfaces — there is no stored UC field for it.
- `related:` is the catchall for cross-references between issue-family artifacts. Soft mentions belong as markdown links in the body, not here.

### Lifecycle and writer ownership

```
draft        → discarded | ready
ready        → discarded | draft | implementing
implementing → blocked | discarded | revising | shipped
revising     → discarded | ready
blocked      → discarded | ready
shipped      → discarded | superseded
discarded    → (terminal)
superseded   → (terminal)
```

Per-status meaning:

- `draft` — Spec is still being shaped; not ready for implementation.
- `ready` — Spec is closed; ready to be picked up by an implementer.
- `implementing` — A coding agent is actively working on the UC.
- `revising` — Implementation paused for in-place spec edit. Re-enters `ready` on re-approval. Cascades: tasks at `progress`/`failing` reset to `pending`; `open`/`pending`/`complete` tasks stay.
- `shipped` — The running system reflects this UC. Forward-path terminal. Cascades: `supersedes:` targets flip `shipped → superseded`.
- `superseded` — A newer UC declared `supersedes: [<this>]` and has shipped. Terminal.
- `discarded` — Abandoned; direction was wrong or UC no longer needed. Terminal. Cascades: related tasks → `discarded`, open review items with `target: usecase/<this>` → `discarded`.
- `blocked` — Implementation-time blocker surfaced; crosscutting. Resolved via `blocked → ready` or `blocked → discarded`.

Writer rules (UC-specific):

- `draft` is the **only** initial status. New UCs are always born at `draft`; everything else is a transition.
- **`implementing → draft` is disallowed.** Once code has started, the UC cannot roll back to pre-spec-closed state. Use `implementing → revising` for in-place edit or `implementing → discarded` for abandonment.
- **`shipped` never returns to `implementing`/`draft`.** Post-ship requirement changes are modeled as either (a) a **new** UC with `supersedes: [usecase/<old>]` — when that new UC ships, the old one flips to `superseded`; or (b) `shipped → discarded` when the feature is being removed from the code.
- **`revising` is in-place.** No new UC is created for the paused spec; the same file is edited, and the ready-gate re-approves `revising → ready`.
- **No mechanical task gate on `ready → implementing` or `implementing → shipped`.** The writer accepts both transitions regardless of whether tasks declaring `implements: [usecase/<this>]` exist or are complete; staging readiness and ship verdicts are author-driven (typically validated through `/a4:run` and roadmap surfaces, not the writer).
- `shipped → superseded` is **automatic** — fires when a successor UC with `supersedes: [<this>]` reaches `shipped`. Do not flip by hand.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Goal` — what the actor wants to accomplish, framed at the user level (the *why*).
- `## Situation` — the trigger / current context. When does this UC apply? What's already happened? Concrete, not abstract.
- `## Flow` — numbered list of user-visible steps. The actor's actions and the system's user-facing responses, **not** internal mechanics.
- `## Expected Outcome` — what success looks like in user-observable terms (timing, content, state change). Used as one input to AC for any task that `implements:` this UC.

**Optional, emit only when there is content for them:**

- `## Validation` — input constraints, limits, required formats. Stays user-visible (length limits, allowed characters, required fields) — internal validation rules belong to spec/architecture.
- `## Error Handling` — what the user sees when things fail. Boundary conditions (empty input, max items, concurrent access, timeouts).
- `## Dependencies` — narrative on which other UCs (or specs / wiki pages) this one depends on, with markdown links. UC ordering is no longer carried in frontmatter, so this section is the only place a UC declares cross-UC prerequisites.
- `## Change Logs` — append-only audit trail when the UC body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `## Log` — optional, hand-maintained status-transition narrative (`YYYY-MM-DD — <from> → <to> — <reason>`). The PostToolUse cascade hook refreshes `updated:` and flips related files but does **not** touch `## Log`; append a bullet by hand if you want the transition recorded in the body.

Unknown H2 headings are tolerated.

## In-situ wiki nudge — when a UC change implies a wiki edit

Authoring or revising a UC frequently has side-effects on wiki pages:

- New actor in `actors:` → `actors.md` `## Roster` row.
- Concept used across 3+ UCs → `domain.md` `## Concepts` glossary entry.
- Scope broadening (problem framing changes) → `context.md` `## Problem Framing` refinement.
- New screen group → `context.md` `## Screens` section + UC `labels:`.
- New non-functional requirement → `nfr.md` `## Requirements` row.

When applying an in-situ wiki edit:

1. Edit the relevant section.
2. Append a dated bullet to the page's `## Change Logs` section (creating the section if absent), with a markdown link to the causing UC.
3. Bump the wiki page's `updated:` frontmatter to today.

When deferring, open a review item with `kind: gap`, `source: self`, `target: [<causing UC path>, <affected wiki basenames>]`. The wiki close guard re-surfaces unresolved impact at session close.

## Splitting a UC — preserve traceability

When a UC turns out to be too large, the protocol is:

1. Confirm the split with the user.
2. Allocate new ids for each child UC.
3. Write each child UC file at `status: draft`.
4. Either delete the parent UC file, or keep it at `status: blocked` with `related: [<child paths>]` if the split history matters (the supersede chain is reserved for shipped predecessors).
5. Update any UC that referenced the parent via `related` (or in `## Dependencies` body prose) to point at the appropriate child.

Splits do **not** flow through the supersede mechanism — supersession presumes the predecessor was at one point shipped.

## Common mistakes (UC-specific)

- **Required section missing** (`## Goal`, `## Situation`, `## Flow`, `## Expected Outcome`).
- **Stray `implemented_by:` field** → the field was retired (a4 v6.0.0); the reverse view of `task.implements:` is now derived on demand. Validators ignore the field, but it should not be re-introduced.

(Universal body-shape rules — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (UC-specific)

- **Don't manually flip cascade-driven statuses.** UC `shipped` → predecessor's `superseded`, UC `discarded` → cascading task / review discards, UC `revising` → task `pending`-reset are all the writer's job.
- **Don't write internal mechanics into the body.** Storage choices, service names, queue strategies, library calls — those live in `architecture.md` or specs. UC body stays at the user level.
- **Don't author a UC for a routine framework-mandated behavior.** UCs describe user-visible interactions; if the only thing to say is "the framework does X," there is no UC there.
- **Don't pack multiple goals into one UC.** Split when the actor's goal forks. One UC = one user-level goal.
