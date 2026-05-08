---
name: arch
description: "Design or revise a4 system architecture."
argument-hint: '<optional: "iterate" to resume; otherwise the skill auto-detects existing a4/architecture.md>'
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Architecture Designer

Takes the use-case set in `a4/usecase/`, the domain model in `a4/domain.md`, and the actor roster in `a4/actors.md`, and designs the system architecture through collaborative dialogue. Writes the result to `a4/architecture.md` as a single wiki page.

## Workspace Layout

Reuse the `a4/` workspace resolved via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/usecase/*.md` — one Use Case per file (from `usecase`).
- `a4/domain.md` — domain concepts, relationships, state transitions.
- `a4/actors.md` — actor roster.
- `a4/nfr.md` — non-functional requirements (optional).
- `a4/context.md` — problem framing / success criteria.

**Outputs:**

- `a4/architecture.md` — single wiki page covering overview, technology stack, external dependencies, components, information flows, interface contracts, test strategy.
- `a4/review/<id>-<slug>.md` — per-finding review items emitted by the wrap-up reviewer.
- `a4/research/<label>.md` — research reports from `api-researcher` (if invoked).

Derived views (consistency tables, UC×component coverage matrix, open-arch-findings dashboard) are produced on demand by grep over frontmatter — not files.

## Modes

- **First Design** — `a4/architecture.md` does not exist. Start from Phase 1 and follow the guided sequence below.
- **Iteration** — `a4/architecture.md` exists. Apply `references/iteration-entry.md` (backlog filter, staleness signals, impact propagation rule).

## Session Task List

Phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` and are created dynamically when entering a phase.

**First Design** — initial tasks:
- `"Step 0: Explore codebase"` → `in_progress`
- `"Phase 1: Technology Stack"` → `pending`
- `"Phase 2: External Dependencies"` → `pending`
- `"Phase 3: Component Design"` → `pending`
- `"Phase 4: Test Strategy"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

**Iteration** — adjust based on the work backlog:
- `"Review open items and backlog"` → `in_progress`
- One task per selected item / area
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

## Workflow

### Step 0: Explore the Codebase

Ground the architecture in reality — project structure, naming conventions, dependencies, build setup, existing test configuration. If a codebase already exists, record the detected technology stack and confirm with the user. Mark "Step 0" completed when done.

### Phases

In **First Design**, run Phases 1 → 4 in order. In **Iteration**, start wherever the user wants. The user controls transitions. Phase-transition fill-in convention for sections is in `${CLAUDE_PLUGIN_ROOT}/authoring/architecture-authoring.md` §Body shape.

| Phase | Focus | Procedure |
|-------|-------|-----------|
| 1 | Technology Stack | `references/phase-tech-stack.md` |
| 2 | External Dependencies | `references/phase-external-deps.md` |
| 3 | Component Design | `authoring/architecture-guide.md` |
| 4 | Test Strategy | `references/test-strategy-guide.md` |

Component names, schema fields, and contract parameters must use `a4/domain.md` terminology.

### Cross-Wiki Edits

When arch work touches another wiki page, follow the in-situ allowance in that page's authoring contract:

- `a4/domain.md` — Domain Model modifications follow `${CLAUDE_PLUGIN_ROOT}/authoring/domain-authoring.md` §Authorship (limited in-situ for non-structural concept work).
- `a4/actors.md` — system-actor additions only, per `${CLAUDE_PLUGIN_ROOT}/authoring/actors-authoring.md` §Authorship.
- `a4/nfr.md` — footnote annotations only, per `${CLAUDE_PLUGIN_ROOT}/authoring/nfr-authoring.md` §Authorship.

### Technical Claim Verification

When recording any non-obvious technical claim, verify before writing it down. Procedure: `references/claim-verification.md`.

### Wrap Up

When the user indicates they're done, run `references/wrap-up.md`: pre-flight consistency check → launch `arch-reviewer` → walk findings → wiki close guard → report.

## File Writing Rules

- **Create `a4/architecture.md`** at the end of Phase 1 with the frontmatter, `## Overview` stub, and the confirmed `## Technology Stack` content.
- **Update** at each phase transition using `Edit` where possible. `Write` only for full rewrites.
- **Change-log entries** — append a dated bullet citing the causing UC / spec / review item.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`arch-reviewer`** — `Agent(subagent_type: "a4:arch-reviewer")`. Reads `a4/` workspace; writes per-finding review items.
- **`api-researcher`** — `Agent(subagent_type: "a4:api-researcher", run_in_background: true)`. Verifies a single technical claim against official docs; writes `a4/research/<label>.md`.

## Non-Goals

- Do not write a separate `design.md` wiki page. The spec explicitly rejects it — `architecture.md` covers design content (stack, components, interfaces, test strategy).
- Do not track per-UC / per-source SHAs in `architecture.md`. The wiki update protocol's `## Change Logs` audit trail (standard markdown link to the causing issue) handles cross-reference consistency without SHA bookkeeping.
- Do not create a research-index file. Use grep over body links.
- Do not emit aggregated review reports. All findings are per-review-item files.
