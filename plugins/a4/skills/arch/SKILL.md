---
name: arch
description: "This skill should be used when the user needs to design or iterate on system architecture — technology stack, external dependencies, component design, information flows, interface contracts, and test strategy. Common triggers include: 'architecture', 'design the system', 'component design', 'tech stack', 'how should we build this', 'system design', 'interface contracts', 'test strategy', 'what tools should we use'. Writes the result as a4/architecture.md (wiki page) following the spec-as-wiki+issues layout."
argument-hint: <optional: \"iterate\" to resume; otherwise the skill auto-detects existing a4/architecture.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Architecture Designer

> **Authoring contract:** the wiki contract for `a4/architecture.md` lives in [`rules/a4-architecture-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-architecture-authoring.md). When this skill edits `domain.md` for in-situ concept work, [`rules/a4-domain-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-domain-authoring.md) §Authorship enumerates the limited-shared in-situ scope. This skill orchestrates — frontmatter shape, body sections, validator behavior are defined in those rules.

Takes the use-case set in `a4/usecase/`, the domain model in `a4/domain.md`, and the actor roster in `a4/actors.md`, and designs the system architecture — technology stack, external dependencies, components, information flows, interface contracts, and test strategy — through collaborative dialogue. Writes the result to `a4/architecture.md` as a single wiki page.

## Workspace Layout

Reuse the `a4/` workspace resolved via `git rev-parse --show-toplevel`. Inputs live at:

- `a4/usecase/*.md` — one Use Case per file (from `usecase`).
- `a4/domain.md` — domain concepts, relationships, state transitions.
- `a4/actors.md` — actor roster.
- `a4/nfr.md` — non-functional requirements (optional).
- `a4/context.md` — problem framing / success criteria.

Output:

- `a4/architecture.md` — single wiki page covering overview, technology stack, external dependencies, components, information flows, interface contracts, test strategy.
- `a4/review/<id>-<slug>.md` — per-finding review items emitted by the wrap-up reviewer.
- `a4/research/<label>.md` — research reports from `api-researcher` (if invoked).

Derived views (consistency tables, UC×component coverage matrix, open-arch-findings dashboard) are **not files**; they are produced on demand by `compass` or by grep over frontmatter.

## Wiki Page Schema

Frontmatter / body sections / `<change-logs>` discipline: see [`rules/a4-architecture-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-architecture-authoring.md).

## Id Allocation

When emitting review items, allocate ids via:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

Determine the mode from the current `a4/` state:

- **First Design** — `a4/architecture.md` does not exist. Start from Phase 1 (Technology Stack) and follow the guided sequence.
- **Iteration** — `a4/architecture.md` exists. Run the Iteration Entry checks below.

### Iteration Entry

Mechanics (filter, backlog presentation, writer calls, footnote rules, discipline) follow [`references/iterate-mechanics.md`](${CLAUDE_PLUGIN_ROOT}/references/iterate-mechanics.md). This section adds only the architecture-specific work.

**Backlog filter:** `target: architecture` OR `architecture` in `wiki_impact`.

**Architecture-specific staleness signals (alongside the backlog):**
1. **New or changed UCs** — compare `architecture.md`'s `<change-logs>` entries against current UC files. UCs not yet cited in any change-log entry are "needs coverage" candidates.
2. **UC ↔ actor / domain drift** — quick pass: for each `<components>` Information Flow subsection in `architecture.md`, check that the referenced UCs and components still exist as current files / component sections.

**Architecture impact propagation rule** — when one area changes, check whether it affects others:
- Technology stack change → do components need restructuring? Do test tools need changing?
- Component change → do information flows still hold? Do interface contracts need updating?
- Test strategy change → does this affect how components are designed for testability?

Surface these cross-area impacts to the user; do not silently assume they're fine. Then recommend a starting point — backlog item, specific new UC, or phase to revisit.

## Session Task List

Use the task list as a live workflow map.

**Naming:** phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` and are created dynamically when entering a phase.

**First Design** — initial tasks at session start:
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

## Step 0: Explore the Codebase

Ground the architecture in reality — project structure, naming conventions, dependencies, build setup, existing test configuration. Reference findings detected during the interview. If a codebase already exists, record the detected technology stack and confirm with the user.

Mark "Step 0" completed when the survey is done.

## Architecture.md Structure

Required and optional body sections, the per-component sub-structure(DB Schema / Information Flow / Interface Contracts), and the `<change-logs>` discipline are defined in [`rules/a4-architecture-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-architecture-authoring.md) §Body shape. Phase-transition fill-in convention used by this skill:

- **`<external-dependencies>`** — populate when the system uses external services.
- **`<component-diagram>`** — populate when the component graph is non-trivial.
- **DB Schema** (inside a `<components>` entry) — only when that component has its own data store.
- **Interface Contracts / Information Flow** (per `<components>` entry) — progressively filled across phases; a mature architecture covers every UC in `a4/usecase/`.

Component names and schema fields must use domain terms from `a4/domain.md`.

## File Writing Rules

- **Create `a4/architecture.md`** at the end of Phase 1 with the frontmatter, `<overview>` stub, and the confirmed `<technology-stack>` content.
- **Update** at each phase transition using `Edit` where possible (preserves structure). `Write` only for full rewrites.
- **Change-log entries** — append a dated bullet citing the causing UC / spec / review item per the rule's `<change-logs>` discipline.
- **`updated:`** — bump on every phase transition or reflected resolution.

## Interview Phases

The architecture covers four areas. In **First Design**, start with Technology Stack and follow the guided sequence. In **Iteration**, start wherever the user wants. The user controls transitions.

### Phase 1: Technology Stack

Select language, framework, platform, and key libraries. For each choice, record the rationale. For lightweight choices — discuss inline and record with a brief rationale. For heavy choices (multiple viable options with significant trade-offs), ask the user: "This seems like a decision worth investigating more deeply. Would you like to run `/a4:research` on the candidates first, then record the conclusion via `/a4:spec` once we've converged?"

spec-trigger signals to watch for during the interview (multi-option enumeration, trade-off language, user uncertainty, prior-spec references) and the anti-patterns that suppress nudges are catalogued at [`references/spec-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/spec-triggers.md).

If a codebase already exists, detect the stack from project files and confirm. Write the initial `architecture.md` at the end of Phase 1.

### Phase 2: External Dependencies

1. **Scan UCs** for external interactions — any UC whose Flow or Outcome references third-party authentication, notifications, file storage, external data sources, etc.
2. **Present the list** with `Used By` (UC markdown links), `Purpose`, and ask for confirmation.
3. **For each confirmed dependency**, clarify:
   - What the system sends/receives (Access Pattern)
   - Constraints (rate limits, pricing tiers, specific provider)
   - Fallback behavior when unavailable
4. Record in `architecture.md`'s `<external-dependencies>` section. Append `<change-logs>` bullets keyed by the causing UCs.

### Phase 3: Component Design

Read `${CLAUDE_SKILL_DIR}/references/architecture-guide.md` for the detailed procedure (component identification, per-component deep dive, DB schema, information flow, interface contracts).

Component names, schema fields, and contract parameters must use `a4/domain.md` terminology.

**Domain Model modifications during arch work.** The in-situ scope (add concept / 1:1 rename / definition wording — inline; split / merge / relationship change / state change — review item with `target: domain`) is enumerated in [`rules/a4-domain-authoring.md`](${CLAUDE_PLUGIN_ROOT}/rules/a4-domain-authoring.md) §Authorship. When emitting a review item, allocate via `allocate_id.py`, write `a4/review/<id>-<slug>.md`, and place a markdown link to the review item inline in the architecture section that surfaced the issue.

### Phase 4: Test Strategy

Read `${CLAUDE_SKILL_DIR}/references/test-strategy-guide.md` for the detailed procedure.

1. **Identify test tiers** — unit (required), integration (architecture-dependent), E2E (UI-dependent).
2. **Select tools per tier** based on app type and tech stack. Use Technical Claim Verification for non-obvious compatibility.
3. **Record** the Test Strategy table with rationale per tier.

## Technical Claim Verification

When writing or confirming any technical claim (API support, library capability, framework constraint, compatibility), verify before recording. Focus on claims whose failure would break implementation.

### Procedure

1. **Check the codebase first** — for claims about the current project's stack, read the actual code, configs, or dependency files.
2. **Launch an `api-researcher` agent** — for external verification, spawn a background `Agent(subagent_type: "a4:api-researcher", run_in_background: true)`. Prompt it with the specific claim and ask it to verify against official documentation.
3. **Continue the interview** — keep working while waiting. Do not transition to the next phase until all pending research results have been received and reflected.
4. **On completion** — the agent writes results to `a4/research/<label>.md`. Read it and apply the verification outcome. Add an inline `(ref: [research/<label>](research/<label>.md))` where the claim is recorded.
5. **Flag uncertainty** — when official documentation is ambiguous, tell the user and ask whether to proceed as an assumption or investigate further.

Maintain the set of research reports under `a4/research/`. Derived indexes (which claims cite which report) come from grep over the body links, not a separately maintained index file.

## Wrapping Up

The architecture ends only when the user says so. When the user indicates they're done:

1. **Pre-flight consistency check** — read `architecture.md` end-to-end. Confirm: every Information Flow UC resolves to an existing UC file; every component's contracts align with its sequence diagrams; every schema field appears in `domain.md`. Resolve obvious gaps before launching the reviewer.

2. **Launch `arch-reviewer`** — spawn `Agent(subagent_type: "a4:arch-reviewer")`. Pass:
   - `a4/` absolute path
   - Prior-session open review items that target `architecture` (so the reviewer can skip duplicates)

   The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md` (using `allocate_id.py`) and returns a summary.

3. **Walk findings** — for each emitted review item (ordered by priority then id), present to the user and resolve or defer:
   - **Fix now** — edit `architecture.md` (and any cross-referenced file). Flip the review item `status: resolved` via `transition_status.py` (which appends the `<log>` entry), and add a dated `<change-logs>` bullet on each modified wiki page per the Wiki Update Protocol.
   - **Defer** — leave `status: open`. Capture the deferral reason in conversation notes / handoff (writer-managed `<log>` only updates on transitions).
   - **Discard** — set `status: discarded` via `scripts/transition_status.py`; the writer records the reason in `<log>`.

4. **Wiki close guard** — for each item that transitioned to `resolved` with non-empty `wiki_impact`, verify the referenced wiki pages contain a `<change-logs>` bullet whose markdown link points at the causing issue. Warn + allow override when missing.

5. **Report** — summarize to the user:
   - Phases completed this session
   - Components added / revised
   - Review items opened / resolved / still open
   - Suggested next step: `/a4:auto-bootstrap` to set up dev environment, or `/a4:roadmap` if bootstrap is already done

### Agent Usage

Context is passed via file paths, not agent memory.

- **`arch-reviewer`** — `Agent(subagent_type: "a4:arch-reviewer")`. Reads `a4/` workspace; writes per-finding review items.
- **`api-researcher`** — `Agent(subagent_type: "a4:api-researcher", run_in_background: true)`. Verifies a single technical claim against official docs; writes `a4/research/<label>.md`.

## Non-Goals

- Do not write a separate `design.md` wiki page. The spec explicitly rejects it — `architecture.md` covers design content (stack, components, interfaces, test strategy).
- Do not track per-UC / per-source SHAs in `architecture.md`. The wiki update protocol's footnote + drift-detector flow handles cross-reference consistency without SHA bookkeeping.
- Do not create a research-index file. Use grep over body links.
- Do not emit aggregated review reports. All findings are per-review-item files.
