# a4 — usecase authoring

A use case at `a4/usecase/<id>-<slug>.md` is a **concrete description of how a user (actor) interacts with the system** to achieve a goal in a specific situation, with a defined flow and an expected outcome. Use cases are the user-facing scope unit — they sit upstream of tasks (which deliver them) and downstream of `context.md` (which frames the problem). They hand off to implementation when their `<flow>` / `<validation>` / `<error-handling>` close enough to drive AC for tasks.

Companion to [`./frontmatter-schema.md §Use case`](./frontmatter-schema.md), `./body-conventions.md`.

## Reading a UC

If only a specific section is needed to answer a question, prefer `extract_section.py <file> <tag>` over loading the whole file.

### Abstraction discipline

Use cases stay at the **user level** — what the actor does, not what the system does internally. A UC that says "the system stores the record in PostgreSQL" is wrong shape; "the user submits the form and sees a confirmation" is right. Internal mechanics belong to `architecture.md` and tasks.

## Frontmatter contract (do not deviate)

```yaml
---
type: usecase
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: draft | ready | implementing | revising | shipped | superseded | discarded | blocked
actors: [<slug>, ...]    # actor slugs as defined in actors.md
depends_on: []           # list of paths to other use cases
spec: []                 # list of paths, e.g. [spec/8-caching-strategy]
supersedes: []           # list of paths to prior UCs this one replaces
implemented_by: []       # AUTO-MAINTAINED — do not hand-edit
related: []              # catchall for cross-references
labels: []               # free-form tags (incl. group slugs like screen-dashboard)
milestone: <optional>    # milestone name (e.g., v1.0)
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `actors:` lists slug identifiers defined as rows in `actors.md`'s `<roster>` section (e.g., `meeting-organizer`, `team-member`, `platform`). New actors flow through `actors.md` first; UC frontmatter references them by slug. Platform-capability UCs typically use `actors: [platform]` or another suitable system actor.
- `depends_on:` lists `usecase/<id>-<slug>` paths the UC needs first (lifecycle blocker). Reverse direction `blocks` is derived on demand.
- `spec:` lists `spec/<id>-<slug>` paths that govern this UC.
- `supersedes:` lists prior UC paths this one replaces. The writer cascades `shipped → superseded` on the listed targets when this UC reaches `shipped`. Do not hand-flip the predecessor's status.
- `implemented_by:` is **auto-maintained** by `../scripts/refresh_implemented_by.py` (back-scan of `task.implements:`). **Never hand-edit.** Used by the `ready → implementing` status gate.
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
- **`ready → implementing` requires `implemented_by:` non-empty.** The UC must have at least one task declaring `implements: [usecase/<this>]`.
- **`implementing → shipped` requires every task in `implemented_by:` to be `complete`.** Enforced by `transition_status.py`.
- `shipped → superseded` is **automatic** — fires when a successor UC with `supersedes: [<this>]` reaches `shipped`. Do not flip by hand.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required (enforced by `../scripts/body_schemas/usecase.xsd`):**

- `<goal>` — what the actor wants to accomplish, framed at the user level (the *why*).
- `<situation>` — the trigger / current context. When does this UC apply? What's already happened? Concrete, not abstract.
- `<flow>` — numbered list of user-visible steps. The actor's actions and the system's user-facing responses, **not** internal mechanics.
- `<expected-outcome>` — what success looks like in user-observable terms (timing, content, state change). Used as one input to AC for any task that `implements:` this UC.

**Optional, emit only when there is content for them:**

- `<validation>` — input constraints, limits, required formats. Stays user-visible (length limits, allowed characters, required fields) — internal validation rules belong to spec/architecture.
- `<error-handling>` — what the user sees when things fail. Boundary conditions (empty input, max items, concurrent access, timeouts).
- `<dependencies>` — narrative on why this UC depends on others (prose backing the `depends_on:` frontmatter list).
- `<change-logs>` — append-only audit trail when the UC body is materially edited post-create (dated bullets with markdown links to the causing issue or spec).
- `<log>` — append-only writer-owned status-transition trail (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — the first status flip writes the first entry. **Never write into `<log>` directly.**

Unknown kebab-case tags are tolerated by the XSD's openContent.

## In-situ wiki nudge — when a UC change implies a wiki edit

Authoring or revising a UC frequently has side-effects on wiki pages:

- New actor in `actors:` → `actors.md` `<roster>` row.
- Concept used across 3+ UCs → `domain.md` `<concepts>` glossary entry.
- Scope broadening (problem framing changes) → `context.md` `<problem-framing>` refinement.
- New screen group → `context.md` `<screens>` section + UC `labels:`.
- New non-functional requirement → `nfr.md` `<requirements>` row.

When applying an in-situ wiki edit:

1. Edit the relevant section tag.
2. Append a dated bullet to the page's `<change-logs>` section (creating the section if absent), with a markdown link to the causing UC.
3. Bump the wiki page's `updated:` frontmatter to today.

When deferring, open a review item with `kind: gap`, `source: self`, `target: <causing UC path>`, `wiki_impact: [<basenames>]`. The wiki close guard re-surfaces unresolved impact at session close.

## Splitting a UC — preserve traceability

When a UC turns out to be too large, the protocol is:

1. Confirm the split with the user.
2. Allocate new ids for each child UC.
3. Write each child UC file at `status: draft`.
4. Either delete the parent UC file, or keep it at `status: blocked` with `related: [<child paths>]` if the split history matters (the supersede chain is reserved for shipped predecessors).
5. Update any UC that referenced the parent via `depends_on` or `related` to point at the appropriate child.

Splits do **not** flow through the supersede mechanism — supersession presumes the predecessor was at one point shipped.

## Common mistakes the validator catches (UC-specific)

- **Required section missing** (`<goal>`, `<situation>`, `<flow>`, `<expected-outcome>`) → `body-xsd`.
- **Hand-edited `implemented_by:`** → not a validator error per se, but the next `refresh_implemented_by.py` run silently overwrites the field. Never depend on hand-written values.

(Universal validator catches — stray body content, attribute-bearing tags, same-tag nesting, H1 in body — are documented in `./body-conventions.md`.)

To validate manually before commit:

```bash
uv run "../scripts/validate_body.py" \
  "<project-root>/a4" --file usecase/<id>-<slug>.md
```

## Don't (UC-specific)

- **Don't hand-edit `implemented_by:`.** Auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't manually flip cascade-driven statuses.** UC `shipped` → predecessor's `superseded`, UC `discarded` → cascading task / review discards, UC `revising` → task `pending`-reset are all the writer's job.
- **Don't write internal mechanics into the body.** Storage choices, service names, queue strategies, library calls — those live in `architecture.md` or specs. UC body stays at the user level.
- **Don't author a UC for a routine framework-mandated behavior.** UCs describe user-visible interactions; if the only thing to say is "the framework does X," there is no UC there.
- **Don't pack multiple goals into one UC.** Split when the actor's goal forks. One UC = one user-level goal.
