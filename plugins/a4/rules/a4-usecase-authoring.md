---
name: a4-usecase-authoring
description: Authoring rules for a4 use case files. Auto-loaded when reading or editing anything under `a4/usecase/`.
paths: ["a4/usecase/**/*.md"]
---

# a4 — usecase authoring guide

A use case at `a4/usecase/<id>-<slug>.md` is a **concrete description
of how a user (actor) interacts with the system** to achieve a goal in
a specific situation, with a defined flow and an expected outcome. Use
cases are the user-facing scope unit — they sit upstream of tasks
(which deliver them) and downstream of `context.md` (which frames the
problem). They are produced by `/a4:usecase` (Socratic interview) or
`/a4:auto-usecase` (forward-shape draft from existing input), and they
hand off to implementation when their `<flow>` / `<validation>` /
`<error-handling>` close enough to drive AC for tasks.

This rule is the working contract for any LLM about to read, draft, or
edit a UC file. The full schema and rationale live in
[`references/frontmatter-schema.md §Use case`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md);
authorship boundaries (who can write what wiki page, when to defer)
live in
[`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md);
body-tag mechanics live in
[`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md).
Read those before deviating from the rules below.

## How to author — always via `/a4:usecase` or `/a4:auto-usecase`

Do **not** hand-craft a UC file with `Write`. Always invoke the
authoring skill so id allocation, slug derivation, frontmatter shape,
body validation, in-situ wiki nudge, and the ready-gate hand-off all
run through the same code path.

- **`/a4:usecase`** — Socratic interview, single UC at a time. Use
  for new workspaces (creates `context.md` first), iteration on the
  existing UC set, or revising an `implementing` UC (flips
  `implementing → revising` via `transition_status.py` first).
- **`/a4:auto-usecase`** — forward-shape draft from existing input
  (e.g., a `spark/<...>.brainstorm.md` or a free-form description).
  Drafts UCs at `status: draft` for the user to refine via
  `/a4:usecase` iteration.

If you must read a UC to answer a question, prefer
`extract_section.py <file> <tag>` over loading the whole file (see
`a4-section-enum.md`).

### Abstraction discipline

Use cases stay at the **user level** — what the actor does, not what
the system does internally. Banned terms and conversion examples live
in `${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/abstraction-guard.md`.
A UC that says "the system stores the record in PostgreSQL" is wrong
shape; "the user submits the form and sees a confirmation" is right.
Internal mechanics belong to `architecture.md` and tasks.

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

- `id` is allocated by `scripts/allocate_id.py` (workspace-global,
  monotonic). Never invent or reuse an id.
- `title` is required and must not be a placeholder; the writer
  rejects `<title>`-shaped strings.
- `actors:` lists slug identifiers defined as rows in `actors.md`'s
  `<roster>` section (e.g., `meeting-organizer`, `team-member`,
  `platform`). New actors flow through `actors.md` first; UC frontmatter
  references them by slug. Platform-capability UCs typically use
  `actors: [platform]` or another suitable system actor.
- `depends_on:` lists `usecase/<id>-<slug>` paths the UC needs first
  (lifecycle blocker). Reverse direction `blocks` is derived on demand.
- `spec:` lists `spec/<id>-<slug>` paths that govern this UC.
- `supersedes:` lists prior UC paths this one replaces. The writer
  cascades `shipped → superseded` on the listed targets when this UC
  reaches `shipped`. Do not hand-flip the predecessor's status.
- `implemented_by:` is **auto-maintained** by
  `scripts/refresh_implemented_by.py` (back-scan of `task.implements:`).
  **Never hand-edit.** Used by the `ready → implementing` status gate.
- `related:` is the catchall for cross-references between issue-family
  artifacts. Soft mentions belong as markdown links in the body, not
  here.
- Path values are plain strings without `.md` and without brackets
  (e.g., `usecase/3-search-history`, not `[usecase/3-search-history.md]`).
- Both `created` and `updated` are unquoted ISO dates. Bump `updated:`
  on every revision; the writer bumps it on status flips.

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
- `revising` — Implementation paused for in-place spec edit. Re-enters
  `ready` on re-approval. Cascades: tasks at `progress`/`failing` reset
  to `pending`; `open`/`pending`/`complete` tasks stay.
- `shipped` — The running system reflects this UC. Forward-path
  terminal. Cascades: `supersedes:` targets flip `shipped → superseded`.
- `superseded` — A newer UC declared `supersedes: [<this>]` and has
  shipped. Terminal.
- `discarded` — Abandoned; direction was wrong or UC no longer needed.
  Terminal. Cascades: related tasks → `discarded`, open review items
  with `target: usecase/<this>` → `discarded`.
- `blocked` — Implementation-time blocker surfaced; crosscutting.
  Resolved via `blocked → ready` or `blocked → discarded`.

Writer rules:

- All status changes after the initial create flow through
  `scripts/transition_status.py`. Skills and humans never write
  `status:` directly post-create.
- `draft` is the **only** initial status. New UCs are always born at
  `draft`; everything else is a transition.
- **`implementing → draft` is disallowed.** Once code has started, the
  UC cannot roll back to pre-spec-closed state. Use `implementing →
  revising` for in-place edit or `implementing → discarded` for
  abandonment.
- **`shipped` never returns to `implementing`/`draft`.** Post-ship
  requirement changes are modeled as either (a) a **new** UC with
  `supersedes: [usecase/<old>]` — when that new UC ships, the old one
  flips to `superseded`; or (b) `shipped → discarded` when the feature
  is being removed from the code.
- **`revising` is in-place.** No new UC is created for the paused
  spec; the same file is edited through `/a4:usecase`, and the Step 6
  ready-gate re-approves `revising → ready`.
- **`ready → implementing` requires `implemented_by:` non-empty.** The
  UC must have at least one task declaring `implements: [usecase/<this>]`.
- **`implementing → shipped` requires every task in `implemented_by:`
  to be `complete`.** Enforced by `transition_status.py`.
- `shipped → superseded` is **automatic** — fires when a successor UC
  with `supersedes: [<this>]` reaches `shipped`. Do not flip by hand.
- `task-implementer` refuses to start on a UC at any status other than
  `ready`. The ready-gate (Step 6 of `/a4:usecase` wrap-up) is the
  hand-off point between spec work and coding.

## Body shape

The body is a sequence of column-0 `<section>...</section>` blocks
(lowercase + kebab-case), with markdown content between the open and
close lines. H1 (`# Title`) is forbidden in the body — title belongs
to frontmatter `title:`. Use H3+ headings inside sections freely.

**Required (enforced by `body_schemas/usecase.xsd`):**

- `<goal>` — what the actor wants to accomplish, framed at the user
  level (the *why*).
- `<situation>` — the trigger / current context. When does this UC
  apply? What's already happened? Concrete, not abstract.
- `<flow>` — numbered list of user-visible steps. The actor's actions
  and the system's user-facing responses, **not** internal mechanics.
- `<expected-outcome>` — what success looks like in user-observable
  terms (timing, content, state change). Used as one input to AC for
  any task that `implements:` this UC.

**Optional, emit only when the conversation produced content for them:**

- `<validation>` — input constraints, limits, required formats. Stays
  user-visible (length limits, allowed characters, required fields) —
  internal validation rules belong to spec/architecture.
- `<error-handling>` — what the user sees when things fail. Boundary
  conditions (empty input, max items, concurrent access, timeouts).
- `<dependencies>` — narrative on why this UC depends on others
  (prose backing the `depends_on:` frontmatter list).
- `<change-logs>` — append-only audit trail when the UC body is
  materially edited post-create (dated bullets with markdown links to
  the causing issue or spec).
- `<log>` — append-only writer-owned status-transition trail
  (`YYYY-MM-DD — <from> → <to> — <reason>`). Starts absent — the first
  status flip writes the first entry. **Never write into `<log>`
  directly.**

Unknown kebab-case tags are tolerated by the XSD's openContent.

### Body-link form

Body cross-references are standard markdown links —
`[text](relative/path.md)` — with the `.md` extension retained
(e.g., `[task/5-render-markdown](../task/5-render-markdown.md)`).
Frontmatter list paths are different (plain strings, no `.md`).

## In-situ wiki nudge — when a UC change implies a wiki edit

Authoring or revising a UC frequently has side-effects on wiki pages:

- New actor in `actors:` → `actors.md` `<roster>` row.
- Concept used across 3+ UCs → `domain.md` `<concepts>` glossary entry.
- Scope broadening (problem framing changes) → `context.md`
  `<problem-framing>` refinement.
- New screen group → `context.md` `<screens>` section + UC `labels:`.
- New non-functional requirement → `nfr.md` `<requirements>` row.

Per `references/wiki-authorship.md`, the `usecase` skill is the
**primary author** for `context.md`, `actors.md`, and `nfr.md`, and
may edit them in-situ. For `domain.md` and `architecture.md`,
**continue** the UC work and emit a review item targeting the upstream
wiki — do not edit those inline.

When applying an in-situ wiki edit:

1. Edit the relevant section tag.
2. Append a dated bullet to the page's `<change-logs>` section
   (creating the section if absent), with a markdown link to the
   causing UC.
3. Bump the wiki page's `updated:` frontmatter to today.

When deferring, open a review item with `kind: gap`, `source: self`,
`target: <causing UC path>`, `wiki_impact: [<basenames>]`. The wiki
close guard re-surfaces unresolved impact at session close.

## Splitting a UC — preserve traceability

When the conversation reveals a UC is too large (read
`${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-splitting.md`
for the splitting guide), the protocol is:

1. Confirm the split with the user.
2. Allocate new ids for each child UC.
3. Write each child UC file at `status: draft`.
4. Either delete the parent UC file, or keep it at `status: blocked`
   with `related: [<child paths>]` if the split history matters
   (the supersede chain is reserved for shipped predecessors).
5. Update any UC that referenced the parent via `depends_on` or
   `related` to point at the appropriate child.

Splits do **not** flow through the supersede mechanism — supersession
presumes the predecessor was at one point shipped.

## Common mistakes the validator catches

- **Stray content outside section blocks** → `body-stray-content`.
  Anything in the body that is not whitespace must live inside a
  `<tag>...</tag>` block.
- **Required section missing** (`<goal>`, `<situation>`, `<flow>`,
  `<expected-outcome>`) → `body-xsd`.
- **Inline or attribute-bearing tags** → `body-tag-invalid`. Open
  and close lines must be on column 0; no attributes; no
  self-closing.
- **Same-tag nesting** → `body-tag-invalid`. Sections do not nest;
  every section sits at the body's top level.
- **H1 in body** → `body-stray-content`. Title is frontmatter-only.
- **Hand-edited `implemented_by:`** → not a validator error per se,
  but the next `refresh_implemented_by.py` run silently overwrites
  the field. Never depend on hand-written values.

To validate manually before commit:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_body.py" \
  "<project-root>/a4" --file usecase/<id>-<slug>.md
```

## Don't

- **Don't hand-edit `status:`.** Use `transition_status.py` (or the
  ready-gate at `/a4:usecase` wrap-up Step 6).
- **Don't hand-edit `<log>`.** It is writer-owned. Every entry comes
  from `transition_status.py`.
- **Don't hand-edit `implemented_by:`.** Auto-maintained by
  `refresh_implemented_by.py` from `task.implements:`.
- **Don't manually flip cascade-driven statuses.** UC `shipped` →
  predecessor's `superseded`, UC `discarded` → cascading task /
  review discards, UC `revising` → task `pending`-reset are all the
  writer's job.
- **Don't write internal mechanics into the body.** Storage choices,
  service names, queue strategies, library calls — those live in
  `architecture.md` or specs. UC body stays at the user level.
- **Don't edit a `revising` UC silently.** When the user asks to edit
  a UC currently at `implementing`, confirm the `implementing →
  revising` flip first; the writer cascades dependent tasks.
- **Don't edit `domain.md` or `architecture.md` in-situ from this
  skill.** Per `wiki-authorship.md`, defer to a review item.
- **Don't author a UC for a routine framework-mandated behavior.**
  UCs describe user-visible interactions; if the only thing to say is
  "the framework does X," there is no UC there.
- **Don't pack multiple goals into one UC.** Split when the actor's
  goal forks. One UC = one user-level goal.
- **Don't promote `draft → ready` by hand.** The wrap-up ready-gate is
  the user's confirmation point.

## After authoring

`/a4:usecase` ends with the wrap-up sequence (explorer review →
reviewer validation → review-item walk-through → wiki close guard →
ready-gate → summary). The skill does not commit; the file (and any
wiki pages updated by the in-situ nudge) is left in the working tree
for the user to commit. The next-step suggestion depends on workspace
state — typically `/a4:domain` (cross-cutting concept extraction) or
`/a4:arch` if `domain.md` already looks current.

## Cross-references

- [`references/frontmatter-schema.md §Use case`](${CLAUDE_PLUGIN_ROOT}/references/frontmatter-schema.md) —
  full field schema, lifecycle, transition rules, validator behavior.
- [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md) —
  primary-author table, in-situ edit allowances, cross-stage feedback
  policy (continue + review item vs stop).
- [`references/body-conventions.md`](${CLAUDE_PLUGIN_ROOT}/references/body-conventions.md) —
  tag form, blank-line discipline, link form,
  `<change-logs>` / `<log>` rules, wiki update protocol.
- [`skills/usecase/SKILL.md`](${CLAUDE_PLUGIN_ROOT}/skills/usecase/SKILL.md) —
  the authoring skill itself; this rule complements it for read/edit
  contexts where the skill is not invoked.
- [`skills/usecase/references/abstraction-guard.md`](${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/abstraction-guard.md) —
  banned-term list and conversion examples for keeping UCs at the
  user level.
- [`skills/usecase/references/usecase-splitting.md`](${CLAUDE_PLUGIN_ROOT}/skills/usecase/references/usecase-splitting.md) —
  the splitting guide.
- `body_schemas/usecase.xsd` — the source of truth for required vs
  optional sections; the `a4-section-enum` rule's bullet block is
  generated from it.
