---
name: usecase
description: "This skill should be used when the user has a vague idea for software but doesn't know exactly what to build, when the user says 'help me figure out what to build', 'what should I make', 'shape this idea', 'use cases', 'gather requirements', 'what do users need', 'break this down', or when a rough idea needs to be shaped into concrete Use Cases through a Socratic interview. Writes per-UC issue files plus wiki pages into <project-root>/a4/ following the spec-as-wiki+issues layout."
argument-hint: <idea or vague concept to turn into use cases, or "iterate" to resume>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Use Case Discovery Facilitator

> **Authoring contracts:** UC files — `${CLAUDE_PLUGIN_ROOT}/authoring/usecase-authoring.md`. Wiki pages this skill primary-authors: `${CLAUDE_PLUGIN_ROOT}/authoring/context-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/authoring/actors-authoring.md`, `${CLAUDE_PLUGIN_ROOT}/authoring/nfr-authoring.md`. Review-item shape: `${CLAUDE_PLUGIN_ROOT}/authoring/review-authoring.md`.

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

Wiki pages are flat at `a4/` root. Issues each get their own file in the matching folder. Derived views (Use Case Diagram, Authorization Matrix, UC Relationships, Open Items dashboard) are produced on demand by `compass` or by grep over frontmatter — not files.

## Id Allocation

Every new issue file gets the next globally-unique id:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

Run this **immediately before** writing a new UC, review item, etc. Ids are monotonic across the whole workspace; do not reuse or renumber.

## Body Conventions

Body heading form, link form, `## Change Logs` audit trail, and the Wiki Update Protocol live in `${CLAUDE_PLUGIN_ROOT}/authoring/body-conventions.md`.

## Modes

- **New workspace** — `a4/` does not exist or has no UC files. Create `a4/context.md` after receiving the idea; proceed through the interview flow.
- **Iteration** — `a4/` already has UC files (or the user said `iterate`). Run `references/iteration-entry.md` on top of `${CLAUDE_PLUGIN_ROOT}/workflows/iterate-mechanics.md`.

Never overwrite existing UC, review, or wiki content without confirming with the user; iteration always preserves prior confirmed work.

## Session Task List

Use the task list as a live workflow map.

**Naming convention:** phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` and are created **dynamically** when entering a phase.

**New workspace** — initial tasks:
- `"Step 1: Receive idea and write context.md"` → `in_progress`
- `"Discovery: Use cases"` → `pending`
- `"Platform capabilities audit"` → `pending`
- `"Wrap Up: Explorer review"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

Domain Model extraction is **out of scope** for this skill — it lives in `/a4:domain`.

**Iteration** — adjust based on the work backlog:
- `"Review open items and backlog"` → `in_progress`
- One task per selected item
- `"Wrap Up: ..."` → `pending` (3 wrap-up tasks)

**Conditional tasks** — add when relevant:
- `"Discovery: Relationship analysis"` — when 5+ UCs are confirmed
- `"UI screen grouping"` — when UI use cases are confirmed
- `"Mock generation"` — when the user agrees to create mocks
- `"Non-functional requirements"` — when the user has NFRs to capture

## Workflow

### Step 1: Receive the Idea (new workspace only)

Restate the idea back in one sentence to confirm understanding. Then immediately:

1. Run `mkdir -p a4/usecase a4/review`.
2. Write `a4/context.md` with frontmatter `type: context`, `updated: <today>`, an `## Original Idea` section quoting the user's input, and a `## Problem Framing` section stub to be filled in as the interview progresses.
3. Tell the user: "I've started `a4/context.md`. UC and wiki files will appear as we confirm them."
4. Mark "Step 1" completed. Mark "Discovery: Use cases" in_progress.

### Steps 2–11: Interview phases

| Step | Phase | Procedure |
|------|-------|-----------|
| 2 | Discovery loop (gaps + actor discovery) | `references/discovery-loop.md` |
| 3 | Progressive UC extraction | `references/progressive-extraction.md` |
| 3a | In-situ wiki nudge | `references/in-situ-wiki-nudge.md` |
| 4 | UC splitting | `references/usecase-splitting.md` |
| 5 | Challenge mode shifts (Contrarian / Simplifier / Reframer) | `references/facilitation-techniques.md` |
| 6 | Similar systems research (on request, after 3+ UCs) | `references/research-procedure.md` |
| 7 | Platform capabilities audit | `references/platform-capabilities-audit.md` |
| 8 | UC relationship analysis (after 5+ UCs) | `references/usecase-relationships.md` |
| 9 | UI screen grouping + (10) mock generation | `references/ui-screen-grouping.md` |
| 11 | Non-functional requirements | `references/nfr-capture.md` |

### Wrap Up

When the user indicates they're done, run `references/wrap-up.md`: explorer → compose new UCs → reviewer → walk findings → wiki close guard → ready-gate → report.

### Revising an `implementing` UC

If the user asks to edit a UC currently at `status: implementing`, follow `references/revising-implementing-uc.md` — confirm the `implementing → revising` transition before editing.

## Agent Usage

Reviews, explorations, and mock generation spawn fresh subagents. Context is passed via file paths, not agent memory.

- **Reviewer:** `Agent(subagent_type: "a4:usecase-reviewer")`. Pass `a4/` path and any prior-session review item ids.
- **Explorer:** `Agent(subagent_type: "a4:usecase-explorer")`. Pass `a4/` path and the expected report output path.
- **Mock generator:** `Agent(subagent_type: "a4:mock-html-generator")`. Pass participating UC paths, layout requirements, and output directory.

**Execution order in Wrap Up:** explorer first, then reviewer.
