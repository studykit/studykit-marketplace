---
name: arch
description: "This skill should be used when the user needs to design or iterate on system architecture — technology stack, external dependencies, component design, information flows, interface contracts, and test strategy. Common triggers include: 'architecture', 'design the system', 'component design', 'tech stack', 'how should we build this', 'system design', 'interface contracts', 'test strategy', 'what tools should we use'. Writes the result as a4/architecture.md (wiki page) following the spec-as-wiki+issues layout."
argument-hint: <optional: \"iterate\" to resume; otherwise the skill auto-detects existing a4/architecture.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Architecture Designer

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

Derived views (consistency tables, UC×component coverage matrix, open-arch-findings dashboard) are **not files**; they render via Obsidian dataview on demand.

## Wiki Page Schema

```yaml
---
kind: architecture
updated: 2026-04-24
---
```

No `revision`, `sources`, or `reflected_files` fields — wiki pages have no lifecycle. Cross-references to UCs / domain concepts / actors are expressed as Obsidian wikilinks (`[[usecase/3-search-history]]`) in body prose. Footnotes + `## Changes` section track updates driven by issue changes, per the Wiki Update Protocol at `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md` (shared across `usecase`, `arch`, and `roadmap`).

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
1. **New or changed UCs** — compare `architecture.md`'s `## Changes` footnotes against current UC files. UCs not yet cited in any arch footnote are "needs coverage" candidates.
2. **UC ↔ actor / domain drift** — quick pass: for each Information Flow section in `architecture.md`, check that the referenced UCs and components still exist as current files / component sections.

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

Ground the architecture in reality — project structure, naming conventions, dependencies, build setup, existing test configuration. Reference what you find during the interview. If a codebase already exists, record the detected technology stack and confirm with the user.

Mark "Step 0" completed when the survey is done.

## Architecture.md Structure

As the interview progresses, grow `a4/architecture.md` with these sections (write on phase transitions; see File Writing Rules below):

```markdown
---
kind: architecture
updated: <today>
---

# Architecture

> Frames the buildable system for the use cases in [[context]], built against the actors in [[actors]] and the concepts in [[domain]].

## Overview

<One-paragraph summary of the architectural approach and key decisions.>

## Technology Stack

| Category | Choice | Rationale |
|----------|--------|-----------|
| Language | TypeScript | … |
| Framework | Next.js | … |

## External Dependencies

<Omit if none.>

| External System | Used By | Purpose | Access Pattern | Fallback |
|----------------|---------|---------|----------------|----------|
| OAuth Provider | [[usecase/1-share-summary]], [[usecase/2-search-history]] | … | … | … |

## Component Diagram

```plantuml
@startuml
component [SessionService] as session
component [RendererService] as renderer
session --> renderer : events
@enduml
```

## Components

### SessionService

**Responsibility:** …

#### DB Schema *(only if data store: yes)*

```plantuml
@startuml
entity "Session" { *id : number | *userId : number | createdAt : datetime }
@enduml
```

#### Information Flow

##### [[usecase/3-search-history]]

```plantuml
@startuml
participant "SessionService" as S
participant "HistoryService" as H
S -> H : request history
@enduml
```

#### Interface Contracts

| Operation | Direction | Request | Response | Notes |
|-----------|-----------|---------|----------|-------|
| createSession | client → SessionService | { userId, title } | { sessionId, status } | sync |

(Repeat per component.)

## Test Strategy

| Tier | Tool | Purpose | Rationale |
|------|------|---------|-----------|
| Unit | Vitest | Component-internal logic | … |
| Integration | @vscode/test-electron | Host environment APIs | … |
| E2E | WebdriverIO + wdio-vscode-service | Full UI interaction | … |

## Changes
```
[^1]: 2026-04-24 — [[usecase/3-search-history]]
[^2]: 2026-04-24 — [[adr/8-caching-strategy]]
```

UC references in Information Flow sections use Obsidian wikilinks — they resolve to `a4/usecase/<id>-<slug>.md`. Component names and schema fields should use domain terms from `a4/domain.md`.

### Required vs Conditional Sections

**Required** (present from First Design onwards): Overview, Technology Stack, Component Diagram, Components (at least one), Test Strategy.

**Conditional:**
- **External Dependencies** — only if the system uses external services.
- **DB Schema** (per component) — only when the component has its own data store.
- **Interface Contracts** (per component pair) — progressively filled as the architecture matures; required once components are stable.
- **Information Flow** (per UC) — progressively filled; a mature architecture covers every UC in `a4/usecase/`.

## File Writing Rules

- **Create `a4/architecture.md`** at the end of Phase 1 with the frontmatter above, Overview stub, and the confirmed Technology Stack.
- **Update** the file at each phase transition using the `Edit` tool where possible (preserves structure). Use `Write` only for full rewrites.
- **Footnote markers** — when a change is driven by a specific UC / ADR / review item (new UC added, component split after review, etc.), add `[^N]` inline in the modified section and append a `## Changes` entry with date + `[[causing-issue]]`. See `${CLAUDE_PLUGIN_ROOT}/references/obsidian-conventions.md` for the full protocol (when to update, how to defer via a review item, close guard).
- **`updated:`** — bump on every phase transition or reflected resolution.

## Interview Phases

The architecture covers four areas. In **First Design**, start with Technology Stack and follow the guided sequence. In **Iteration**, start wherever the user wants. The user controls transitions.

### Phase 1: Technology Stack

Select language, framework, platform, and key libraries. For each choice, record the rationale. For lightweight choices — discuss inline and record with a brief rationale. For heavy choices (multiple viable options with significant trade-offs), ask the user: "This seems like a decision worth investigating more deeply. Would you like to run `/a4:research` on the candidates first, then record the conclusion via `/a4:adr` once we've converged?"

ADR-trigger signals to watch for during the interview (multi-option enumeration, trade-off language, user uncertainty, prior-ADR references) and the anti-patterns that suppress nudges are catalogued at [`references/adr-triggers.md`](${CLAUDE_PLUGIN_ROOT}/references/adr-triggers.md).

If a codebase already exists, detect the stack from project files and confirm. Write the initial `architecture.md` at the end of Phase 1.

### Phase 2: External Dependencies

1. **Scan UCs** for external interactions — any UC whose Flow or Outcome references third-party authentication, notifications, file storage, external data sources, etc.
2. **Present the list** with `Used By` (UC wikilinks), `Purpose`, and ask for confirmation.
3. **For each confirmed dependency**, clarify:
   - What the system sends/receives (Access Pattern)
   - Constraints (rate limits, pricing tiers, specific provider)
   - Fallback behavior when unavailable
4. Record in `architecture.md`'s External Dependencies section. Add a `## Changes` footnote keyed by the causing UCs.

### Phase 3: Component Design

Read `${CLAUDE_SKILL_DIR}/references/architecture-guide.md` for the detailed procedure (component identification, per-component deep dive, DB schema, information flow, interface contracts).

Component names, schema fields, and contract parameters must use `a4/domain.md` terminology.

**Domain Model modifications during arch work.** Cross-cutting domain authorship is `/a4:domain`'s job; arch's role is to flag mismatches and apply *simple* edits inline. The full workspace-wide authorship + cross-stage feedback policy is at [`references/wiki-authorship.md`](${CLAUDE_PLUGIN_ROOT}/references/wiki-authorship.md); the table below is the arch-specific b3 instance:

| Change shape | Owner | What arch does |
|---|---|---|
| New concept / new attribute on existing concept | arch | Edit `a4/domain.md` directly. Footnote + `## Changes` entry pointing at `[[architecture#<section>]]`. Bump `updated:`. |
| 1:1 rename of an existing concept | arch | Edit `a4/domain.md` directly. Update every existing reference in the same file. Footnote + `## Changes`. Bump `updated:`. |
| Definition wording / clarification on an existing concept | arch | Edit `a4/domain.md` directly. Footnote + `## Changes`. Bump `updated:`. |
| Concept split / merge | `/a4:domain` | Allocate a review item: `kind: gap`, `target: domain`, `wiki_impact: [domain]`, `source: self`, body summarizes the proposed split/merge with arch's rationale. **Do not edit `domain.md`.** Continue arch using a placeholder term; the user will run `/a4:domain iterate` later to land the structural change. |
| Relationship add / remove / cardinality change | `/a4:domain` | Same as split/merge — emit a review item targeting `domain`; do not edit. |
| State or transition added / removed | `/a4:domain` | Same — emit a review item; do not edit. |

When emitting a review item under this table, allocate via `allocate_id.py` and write `a4/review/<id>-<slug>.md`. Place a wikilink to the new review item inline in the architecture section that surfaced the issue, so the user can find it during `/a4:domain iterate`.

The boundary is: *content changes* (add a concept, rename, clarify) are inline; *structural changes* (split, merge, relationship topology, state topology) require a focused cross-cutting pass that arch does not attempt mid-component-design.

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
4. **On completion** — the agent writes results to `a4/research/<label>.md`. Read it and apply the verification outcome. Add an inline `(ref: [[research/<label>]])` where the claim is recorded.
5. **Flag uncertainty** — when official documentation is ambiguous, tell the user and ask whether to proceed as an assumption or investigate further.

Maintain the set of research reports under `a4/research/`. Derived indexes (which claims cite which report) come from Obsidian backlinks, not a separately maintained index file.

## Wrapping Up

The architecture ends only when the user says so. When the user indicates they're done:

1. **Pre-flight consistency check** — read `architecture.md` end-to-end. Confirm: every Information Flow UC resolves to an existing UC file; every component's contracts align with its sequence diagrams; every schema field appears in `domain.md`. Resolve obvious gaps before launching the reviewer.

2. **Launch `arch-reviewer`** — spawn `Agent(subagent_type: "a4:arch-reviewer")`. Pass:
   - `a4/` absolute path
   - Prior-session open review items that target `architecture` (so the reviewer can skip duplicates)

   The reviewer emits one review item file per finding into `a4/review/<id>-<slug>.md` (using `allocate_id.py`) and returns a summary.

3. **Walk findings** — for each emitted review item (ordered by priority then id), present to the user and resolve or defer:
   - **Fix now** — edit `architecture.md` (and any cross-referenced file). Set the review item `status: resolved`, append a `## Log` entry, and add a footnote marker on each modified wiki page per the Wiki Update Protocol.
   - **Defer** — leave `status: open`; add a `## Log` entry noting the deferral reason.
   - **Discard** — set `status: discarded` via `scripts/transition_status.py`; the writer records the reason in `## Log`.

4. **Wiki close guard** — for each item that transitioned to `resolved` with non-empty `wiki_impact`, verify the referenced wiki pages contain a footnote whose payload wikilinks the causing issue. Warn + allow override when missing.

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

- Do not write a separate `design.md` wiki page. The ADR explicitly rejects it — `architecture.md` covers design content (stack, components, interfaces, test strategy).
- Do not track per-UC / per-source SHAs in `architecture.md`. The wiki update protocol's footnote + drift-detector flow handles cross-reference consistency without SHA bookkeeping.
- Do not create a research-index file. Use Obsidian backlinks.
- Do not emit aggregated review reports. All findings are per-review-item files.
