---
name: usecase
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'use cases', 'gather requirements', 'what do users need', 'break this down', or when a rough idea needs to be shaped into concrete Use Cases through a Socratic interview. Writes per-UC issue files plus wiki pages into <project-root>/a4/ following the spec-as-wiki+issues layout."
argument-hint: <idea or vague concept to turn into use cases, or "iterate" to resume>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Use Case Discovery Facilitator

A Socratic interviewer that helps users discover what to build through one-question-at-a-time dialogue. The conversation progressively produces **Use Cases** — concrete descriptions of how users interact with the system, grounded in real situations — together with the cross-cutting wiki pages that frame them (context, actors, domain, NFRs).

Discover use cases for: **$ARGUMENTS**

## Workspace Layout

All artifacts live inside the project's `a4/` workspace (resolve via `git rev-parse --show-toplevel`). One project = one `a4/` = one topic; no topic prefix appears in filenames or folders.

```
a4/
  context.md                  # Wiki: original idea, problem framing, success criteria
  actors.md                   # Wiki: actor roster (type, role, description)
  domain.md                   # Wiki: concepts, relationships, state transitions
  nfr.md                      # Wiki: non-functional requirements (optional)
  usecase/
    3-search-history.md       # Issue: one Use Case per file
  review/
    6-missing-validation.md   # Issue: open findings, gaps, questions
  research/                   # Optional: similar-systems research reports
  mock/                       # Optional: HTML mocks per screen group
```

Wiki pages (`context.md`, `actors.md`, `domain.md`, `nfr.md`) are flat at `a4/` root. Issues (UC, review) each get their own file in the matching folder. Derived views (Use Case Diagram, Authorization Matrix, UC Relationships, Open Items dashboard) are **not files** — they render on demand from frontmatter via Obsidian dataview.

## Frontmatter Schemas

**Wiki page** — `context.md`, `actors.md`, `domain.md`, `nfr.md`:
```yaml
---
kind: context | actors | domain | nfr
updated: 2026-04-24
---
```

**Use Case** — `usecase/<id>-<slug>.md`:
```yaml
---
id: 3
title: Search history
status: draft | ready | implementing | revising | shipped | superseded | discarded | blocked
actors: [meeting-organizer, team-member]
depends_on: [usecase/1-share-summary]
supersedes: []
implemented_by: []   # auto-maintained by refresh_implemented_by.py
related: []
labels: [search, ui]
milestone: v1.0
created: 2026-04-24
updated: 2026-04-24
---
```

Omit empty fields or leave `[]`. `milestone` is optional until the plan phase assigns one. Paths are plain strings (no brackets, `.md` omitted) for dataview compatibility. Body uses Obsidian wikilinks (`[[...]]`) and embeds (`![[...]]`).

UC lifecycle has eight states:

- `draft` — spec still being shaped (initial state).
- `ready` — spec closed; waiting for an implementer to pick it up.
- `implementing` — a `task-implementer` agent is working on it.
- `revising` — implementation paused for in-place spec edit. Re-enters `ready` on re-approval.
- `shipped` — the running system reflects this UC. Forward-path terminal.
- `superseded` — replaced by a newer UC that declared `supersedes: [<this>]` and shipped. Terminal.
- `discarded` — direction abandoned. Terminal. Related tasks and open review items cascade to `discarded`.
- `blocked` — implementation-time blocker; crosscutting. Resolved via `blocked → ready` or `blocked → discarded`.

**All status changes flow through `scripts/transition_status.py`.** Do not hand-edit `status:` / `updated:` / `## Log` entries — the writer owns them.

**`implementing → draft` is disallowed.** Once code has started, use `implementing → revising` for in-place spec edit, or `implementing → discarded` to abandon the direction. `shipped` never returns to `implementing` or `draft` — post-ship changes are either a new UC with `supersedes:` or `shipped → discarded` when removing the feature.

**Review item** — `review/<id>-<slug>.md` (used by wrap-up and the in-situ nudge):
```yaml
---
id: 6
kind: finding | gap | question
status: open | in-progress | resolved | discarded
target: usecase/3-search-history       # omit for cross-cutting
source: self | usecase-reviewer | drift-detector | task-implementer
wiki_impact: [domain, actors]          # basenames of wiki pages needing updates; [] when none
priority: high | medium | low
labels: []
created: 2026-04-24
updated: 2026-04-24
---
```

Review status transitions flow through `transition_status.py` too (`open → in-progress → resolved` / `discarded`). A review item with `target: usecase/<X>` automatically cascades to `discarded` when its target UC is discarded.

## Id Allocation

Every new issue file gets the next globally-unique id:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Run this **immediately before** writing a new UC, review item, etc. Ids are monotonic across the whole workspace (GitHub-issue semantics); do not reuse or renumber.

## Obsidian Conventions

Wikilink / embed syntax, the footnote audit trail, and the Wiki Update Protocol (when a wiki page needs an update, how to apply one, how to defer via a review item, and the close guard) are documented in `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md`. That reference is shared by `usecase`, `arch`, and `roadmap`. Read it once.

Key rules this skill invokes below:

- Body prose uses wikilinks (`[[usecase/3-search-history]]`) and embeds (`![[usecase/3-search-history]]`). Frontmatter paths stay bracket-free per [frontmatter-schema.md](../../references/frontmatter-schema.md).
- When a confirmed UC / actor / concept change affects a wiki page, update the wiki page in place: leave a `[^N]` footnote in the modified section, append a `## Changes` line pointing at the causing issue, and bump the wiki page's `updated:`.
- If the user defers a wiki update, open a review item with `wiki_impact:` set; the close guard re-surfaces it at session close.

## Modes

Determine the mode from `$ARGUMENTS` and the current `a4/` state:

- **New workspace** — `a4/` does not exist or has no UC files. Create `a4/context.md` after receiving the idea; proceed through the interview flow.
- **Iteration** — `a4/` already has UC files (or the user said `iterate`). Run the iteration entry procedure in `${CLAUDE_SKILL_DIR}/references/iteration-entry.md`.

Never overwrite existing UC, review, or wiki content without confirming with the user; iteration always preserves prior confirmed work.

## Session Task List

Use the task list as a live workflow map. The user should be able to check the task list at any point and understand exactly where they are and what remains.

**Naming convention:** phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>`. Sub-tasks are created **dynamically** when entering a phase — not all upfront.

**Task lifecycle:**
- Mark phase-level task `in_progress` when entering the phase.
- Create sub-tasks as work items are identified within the phase.
- Mark sub-tasks `completed` as each is confirmed.
- Mark phase-level task `completed` when all sub-tasks are done.
- If the user navigates back to a completed phase, set it back to `in_progress`.

**New workspace** — create phase-level tasks at session start:
- `"Step 1: Receive idea and write context.md"` → `in_progress`
- `"Discovery: Use cases"` → `pending`
- `"Platform capabilities audit"` → `pending`
- `"Wrap Up: Explorer review"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

Domain Model extraction is **out of scope** for this skill — it lives in `/a4:domain`. The Discovery loop captures actors and per-UC bodies; cross-cutting concept/relationship/state work happens after the UC set settles, in a separate skill invocation.

**Iteration** — adjust based on the work backlog:
- `"Review open items and backlog"` → `in_progress`
- One task per selected item (e.g., `"Resolve review/6: missing validation on UC-3"`)
- `"Wrap Up: Explorer review"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

**Conditional tasks** — add when they become relevant:
- `"Discovery: Relationship analysis"` — when 5+ UCs are confirmed
- `"UI screen grouping"` — when UI use cases are confirmed
- `"Mock generation"` — when the user agrees to create mocks
- `"Non-functional requirements"` — when the user has NFRs to capture

## Interview Flow

### 1. Receive the Idea (new workspace only)

Restate the idea back in one sentence to confirm understanding. Then immediately:

1. Run `mkdir -p a4/usecase a4/review`.
2. Write `a4/context.md` with frontmatter `kind: context`, `updated: <today>`, a `# Context` heading, an **Original Idea** section quoting the user's input, and a **Problem Framing** section stub to be filled in as the interview progresses.
3. Tell the user: "I've started `a4/context.md`. UC and wiki files will appear as we confirm them."
4. Mark "Step 1" completed. Mark "Discovery: Use cases" in_progress.

### 2. Discovery Loop

Uncover enough context to write concrete Use Cases by targeting four gaps: **What's happening now?** (current situation/trigger), **Who's involved?** (people → actors), **What should change?** (desired action → flow), **What does success look like?** (outcome). Follow the conversation naturally, targeting whichever gap is most unclear.

**Actor discovery.** When the conversation reveals a new person or system:
1. Confirm the actor with the user (name, type `person`/`system`, role — privilege level, short description).
2. If `a4/actors.md` does not exist, create it with frontmatter `kind: actors`, `updated: <today>`, and an empty Actors table.
3. Add the confirmed actor to the table. Use a slug identifier (`meeting-organizer`, `team-member`) that UC frontmatter can reference in `actors: [...]`.
4. If the new actor justifies a wiki update (it usually does on first appearance), append a footnote marker + `## Changes` entry as described in the Wiki Update Protocol.

### 3. Progressive Use Case Extraction

When the conversation reveals enough context, draft a Use Case and present it to the user for confirmation. Every UC has five required fields: **Actor**, **Goal**, **Situation**, **Flow**, **Expected Outcome**. Abstraction must stay at the user level — read `${CLAUDE_SKILL_DIR}/references/abstraction-guard.md` for the banned-term list and conversion examples.

**How to present:**

> Based on what you've described, here's a Use Case:
>
> **UC-draft. Share meeting summary**
> - **Actor:** Meeting organizer
> - **Goal:** Share key decisions with absent teammates quickly
> - **Situation:** Just finished a 30-minute meeting; absent teammates need the outcome
> - **Flow:** 1. Open the meeting record … 5. Send to the team channel
> - **Expected Outcome:** Absent teammates receive a 3-line summary within minutes; organizer spends < 2 minutes instead of 20
>
> Does this capture it? Anything to adjust?

After the user confirms the core UC, **immediately drill into precision**:

- **Validation** — input constraints, limits, required formats (user-visible, not system-internal).
- **Error handling** — what the user sees when things fail.
- **Boundary conditions** — empty input, maximum items, concurrent access, timeouts.

Record these in the UC's body as `## Validation` / `## Error handling` sections. Both are optional — omit when the UC has no meaningful constraints or failure modes.

**Write the UC file on confirmation:**

1. Derive a kebab-case slug from the title (`Share meeting summary` → `share-summary`).
2. Run the id allocator (see Id Allocation) to get the next id `N`.
3. Write `a4/usecase/<N>-<slug>.md` with the frontmatter schema above. Body sections: `## Goal`, `## Situation`, `## Flow` (numbered list), `## Expected Outcome`, and optional `## Validation` / `## Error handling` / `## Dependencies` / `## Log`.
4. Create a task `"Discovery: UC-<N> <title>"` and mark it completed.
5. **In-situ nudge** (see next subsection) — offer to capture wiki impact if the UC introduces new actors, new concepts, or changes framing.

### 3a. In-Situ Wiki Nudge

After writing a UC file (and after any other significant issue change — new actor, domain concept, NFR, etc.), check whether the change affects existing wiki pages:

- New actor → `actors.md` likely needs an entry.
- Concept used across 3+ UCs → `domain.md` needs a glossary entry.
- Scope broadening → `context.md` Problem Framing may need refinement.

If yes, present the candidate updates and ask the user to confirm. For each confirmed update:

1. Edit the affected wiki page — update the section, append a footnote marker `[^N]` inline, append a `## Changes` line with today's date and an Obsidian wikilink to the causing issue.
2. Bump the wiki page's `updated:` frontmatter to today.

Minor edits (typo, metadata-only) skip the nudge. Use judgment; the rule is "significant changes only — create, status transition, resolve."

If the user defers the update, open a review item instead:

1. Allocate id, write `a4/review/<id>-<slug>.md` with `kind: gap`, `status: open`, `source: self`, `target: <causing issue path>`, and `wiki_impact: [<affected wiki basenames>]`.
2. The wiki close guard (run at session close and by drift detection) surfaces the unresolved impact later.

### 4. Use Case Splitting

After a UC is confirmed, evaluate whether it is too large. Read `${CLAUDE_SKILL_DIR}/references/usecase-splitting.md` for the full splitting guide.

When splitting a UC that has already been written to disk:
1. Confirm the split with the user.
2. Allocate new ids for each child UC.
3. Write each child UC file.
4. Delete the parent UC file (or keep it with `status: blocked` and `supersedes`-like `related: [<child paths>]` if the split history matters).
5. Update any UC that referenced the parent via `depends_on` or `related`.

### 5. Challenge Mode Shifts

After sustained questioning in one direction, shift perspective to break habitual thinking. Three modes: Contrarian, Simplifier, Reframer. For detailed techniques and trigger conditions, read `${CLAUDE_SKILL_DIR}/references/facilitation-techniques.md`.

### 6. Similar Systems Research (on request)

Research is **not automatic** — only trigger when the user explicitly asks or agrees to a one-time nudge after 3+ confirmed use cases. For the full procedure (nudge timing, background agent launch, result handling), read `${CLAUDE_SKILL_DIR}/references/research-procedure.md`. Reports land in `a4/research/<label>.md`.

### 7. Platform Capabilities Audit

Mark "Discovery: Use cases" as `completed`. Mark "Platform capabilities audit" as `in_progress`.

After all primary UCs are confirmed, perform a final audit for implicit platform capabilities — shared behaviors that multiple UCs assume but no UC defines (message input, conversation display, navigation, session restore, etc.).

1. **Scan all UC flows** for user actions that appear across 3+ UCs but aren't themselves covered by any UC.
2. **Present findings** to the user as a table (Assumed Capability | Referenced By | Example flow text). Ask whether to create UCs.
3. **Create UCs** for confirmed gaps the same way as any other UC (allocate id, write `usecase/<id>-<slug>.md`). These UCs use `actors: [platform]` or a suitable system actor.
4. Skip silently if no gaps are found.

### 8. UC Relationship Analysis

After 5+ UCs are confirmed, analyze and present relationships. Read `${CLAUDE_SKILL_DIR}/references/usecase-relationships.md`. Relationships are captured as:

- **Dependencies** — `depends_on: [usecase/<id>-<slug>]` in the dependent UC's frontmatter.
- **Reinforcements** — `related: [usecase/<id>-<slug>]` (soft ties) or body wikilinks.
- **Groups** — `labels: [<group-slug>]`. Group definitions live as body text in `context.md` when useful.

No separate section file is written — these are derived views, rendered by dataview or by compass.

### 9. UI Screen Grouping (if UI UCs exist)

After UCs are confirmed, group UI-related UCs by screen. For each screen:
1. Propose a group label (e.g., `screen-dashboard`) and add it to `labels:` in the involved UCs.
2. Record the screen-navigation narrative as a section in `context.md` (or a dedicated `## Screens` section), with wikilinks back to the participating UCs.

### 10. Mock Generation (optional, per screen group)

For each confirmed screen group, optionally generate an HTML mock at `a4/mock/<screen-slug>/`:

1. Invoke `Agent(subagent_type: "a4:mock-html-generator")` with UCs in the group, layout requirements, and output path.
2. Present the mock and gather feedback.
3. Refine UCs from mock feedback.

Mocks are suggested, not required.

### 11. Non-Functional Requirements (optional)

Ask the user once:

> Are there non-functional requirements? Performance targets, security, scalability, accessibility, compliance. If not, we can skip this.

If yes, write `a4/nfr.md` with frontmatter `kind: nfr`, `updated: <today>`, and a table of requirements (Description | Affected UCs via wikilinks | Measurable criteria). Skip creating the file when there are no NFRs.

## Wrapping Up

The interview ends only when the user says so. Never conclude on your own — even if all gaps seem covered, the user may want to go deeper.

When the user indicates they're done, mark `"Platform capabilities audit"` (or whichever phase task is currently `in_progress`) as `completed`, then proceed to **End Iteration** in `${CLAUDE_SKILL_DIR}/references/session-closing.md`. The short version:

1. Launch `Agent(subagent_type: "a4:usecase-explorer")` to surface additional perspectives.
2. Reflect accepted candidates (new UC files as above).
3. Launch `Agent(subagent_type: "a4:usecase-reviewer")`. The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md`.
4. Walk the user through each emitted review item. Resolve in place (edit the target UC / wiki page, set `status: resolved` in the review item, add `## Log` entries) or defer (leave `status: open`).
5. **Wiki close guard** — for each resolved review item with non-empty `wiki_impact`, verify each referenced wiki page has a footnote whose payload wikilinks the causing issue. Warn + allow override when missing.
6. **Ready-gate.** Before the final summary, per-UC ask the user whether each UC still at `status: draft` or `status: revising` is ready to hand off (or re-hand-off) to implementation. Accept natural-language answers:
   - yes / ok / 확정 / `"mark ready"` → call the writer:
     ```bash
     uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
       "$(git rev-parse --show-toplevel)/a4" \
       --file "usecase/<id>-<slug>.md" --to ready \
       --reason "user confirmed ready-gate"
     ```
   - no / `"아직"` / `"still iterating"` / silence → leave at current status.

   Only `draft` and `revising` UCs are offered. UCs at `ready`, `implementing`, `shipped`, `superseded`, `discarded`, or `blocked` are skipped. `task-implementer` refuses to start on a UC at any status other than `ready`, so this gate is the hand-off point between spec work and coding.
7. Report a summary: UCs confirmed, UCs flipped to `ready`, wiki pages written, review items opened, review items resolved. Suggest `/a4:domain` as the next step (cross-cutting concept extraction). If `a4/domain.md` already exists and looks current, suggest `/a4:arch` instead.

## Revising an `implementing` UC

When the user asks to edit a UC that is currently `status: implementing` (e.g., "UC 5 Flow 수정해줘", "fix the spec for UC-7"), do not silently edit the body. Instead:

1. **Confirm** the transition: "UC X is currently `implementing`. Edit in-place means flipping to `revising` (pauses code work; resets `implementing`/`failing` tasks to `pending`; `complete` tasks stay). OK?"
2. On user confirmation, call the writer:
   ```bash
   uv run "${CLAUDE_PLUGIN_ROOT}/scripts/transition_status.py" \
     "$(git rev-parse --show-toplevel)/a4" \
     --file "usecase/<id>-<slug>.md" --to revising \
     --reason "user-triggered spec edit"
   ```
   The script cascades task status automatically.
3. Walk through the edit with the user (Flow, actors, Validation, Error handling) — same protocol as iteration on a `draft` UC. When the user indicates the spec is done, Step 6 ready-gate flips `revising → ready`.

If `task-implementer` previously triggered the flip (a review item with `source: task-implementer` exists for this UC), walk those review items first — they describe exactly what ambiguity blocked implementation.

### Agent Usage

Reviews, explorations, and mock generation spawn fresh subagents. Context is passed via file paths, not agent memory.

- **Reviewer:** `Agent(subagent_type: "a4:usecase-reviewer")`. Pass `a4/` path and any prior-session review item ids (so the reviewer can check whether prior findings were addressed).
- **Explorer:** `Agent(subagent_type: "a4:usecase-explorer")`. Pass `a4/` path and the expected report output path (`a4/research/<label>.md`).
- **Mock generator:** `Agent(subagent_type: "a4:mock-html-generator")`. Pass participating UC paths, layout requirements, and output directory.

**Execution order in Wrap Up:** explorer first (find gaps and new UC candidates), then reviewer (validates the full set).
