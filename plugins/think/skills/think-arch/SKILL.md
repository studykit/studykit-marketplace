---
name: think-arch
description: "This skill should be used when the user needs to design or iterate on system architecture — technology stack, component design, information flows, interface contracts, and test strategy. Common triggers include: 'architecture', 'design the system', 'component design', 'tech stack', 'how should we build this', 'system design', 'interface contracts', 'test strategy', 'what tools should we use'. Also applicable when use cases from think-usecase need to be turned into a buildable architecture."
argument-hint: <path to .usecase.md file, or existing .arch.md file for iteration>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Architecture Designer

Takes use cases (from think-usecase) and designs the system architecture — technology stack, external dependencies, components, information flows, interface contracts, and test strategy — through collaborative dialogue.

## Modes

- **No existing `.arch.md`** → **First Design**. Start from Phase 1 (Technology Stack) and follow the guided sequence.
- **Existing `.arch.md`** → run Iteration Mode entry checks (feedback, source changes, impact assessment):
  - **Additive Feature** → new UCs fit within existing architecture. Add information flows and interface contracts only.
  - **Iteration** → architecture changes needed. The user chooses which area to work on, or starts from Phase 1 for a fundamental rethink.

**Impact propagation rule:** when something changes in one area, check whether it affects others:
- Technology stack change → do components need restructuring? Do test tools need changing?
- Component change → do information flows still hold? Do interface contracts need updating?
- Test strategy change → does this affect how components are designed for testability?

Always surface these cross-area impacts to the user rather than silently assuming they're fine.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/`:

1. **Full path** — extract the slug from the filename (e.g., `A4/chat-app.usecase.md` → `chat-app`), then scan for related files: `A4/*<slug>*.usecase.md` and `A4/*<slug>*.arch.md`
2. **Partial match** — glob for `A4/*<argument>*.usecase.md` and `A4/*<argument>*.arch.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading.

**Mode detection:**
- If the target `.arch.md` already exists → read the arch file, then run the **Existing Arch Entry** checks below.
- If only use case files are found (no existing arch) → start from Phase 1.

The source reference in the output file should be placed as a blockquote under the title heading, linking to all input files (see output template for format).

**Existing Arch Entry:** Perform these checks to assess the current state and determine where to start.

### 1. Source Usecase Changes

Compare the stored `sha` in arch frontmatter against the current file:
- Run `git hash-object <usecase-file-path>` to get the current SHA.
- If SHA matches → no changes, skip.
- If SHA differs → run `git diff <stored-sha> <current-sha>` to see exactly what changed. Also read the usecase's history file for context.
- Present the changes to the user and walk through impact on architecture.
- After reflecting, update `sources` in frontmatter. If content changed, **increment `revision`** and update `revised` timestamp.

### 2. Unreflected Reports

Check for report files not listed in `reflected_files`:

- `A4/<topic-slug>.arch.review-*.md` (review reports)
- `A4/<topic-slug>.bootstrap.md` (bootstrap reports — issues where `Stage: arch`)
- `A4/<topic-slug>.integration-report.r*.md` (integration reports — issues where `Stage: arch`)
- `A4/<topic-slug>.plan.md` (check for blocked status with arch-level issues)
- `A4/<topic-slug>.test-report.c*.md` (check for failures diagnosed as arch-level)

For integration reports, prioritize issues where the diagnosis stage is **arch**. For plan deviations, read the Deviation Note to determine if the root cause is an architecture assumption that doesn't hold.

### 3. Impact Assessment

When source usecase changes include **new UCs**, assess whether the existing architecture can accommodate them:

- Do the new UCs require **new components** not present in the current design?
- Do they introduce **new external dependencies**?
- Do they require **technology stack changes**?
- Do they fundamentally change **information flows** between existing components?

**If yes to any** → full **Iteration** path. Recommend which areas need rework.
**If no** → **Additive Feature** path. The new UCs fit within existing components and patterns — only new information flows and interface contracts are needed.

Present the assessment to the user and let them confirm the path.

### 4. Recommend Starting Point

Analyze the collected feedback and open items. Recommend which area to work on first, with rationale. The user can follow the recommendation or choose a different starting point.

## Session Task List

Use the task list as a live workflow map. The user should be able to check the task list at any point and understand exactly where they are and what remains.

### Naming Convention

Tasks use a prefix to show structure. Phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` format.

- Phase-level: `"Phase 1: Technology Stack"`
- Sub-task: `"Phase 1: Select language/framework"`, `"Phase 1: Evaluate key libraries"`

Sub-tasks are created **dynamically** when entering a phase — not all upfront. For example, Phase 3 sub-tasks are created per component after components are identified.

### Task Lifecycle

- Mark phase-level task `in_progress` when entering the phase.
- Create sub-tasks as work items are identified within the phase.
- Mark sub-tasks `completed` as each is confirmed.
- Mark phase-level task `completed` when all sub-tasks are done.
- If the user navigates back to a completed phase, set it back to `in_progress`.

### Initial Task Lists

Create phase-level tasks at session start. Sub-tasks are added dynamically during work.

**First Design:**
- `"Step 0: Explore codebase"` → `in_progress`
- `"Phase 1: Technology Stack"` → `pending`
- `"Phase 2: External Dependencies"` → `pending`
- `"Phase 3: Component Design"` → `pending`
- `"Phase 4: Test Strategy"` → `pending`
- `"Wrap Up: Save progress"` → `pending`
- `"Wrap Up: Review (arch-reviewer)"` → `pending`
- `"Wrap Up: Record open items & commit"` → `pending`

**Iteration:**
- `"Review open items and backlog"` → `in_progress`
- One task per selected area (e.g., `"Phase 2: Revise external dependencies"`)
- `"Wrap Up: Save progress"` → `pending`
- `"Wrap Up: Review (arch-reviewer)"` → `pending`
- `"Wrap Up: Record open items & commit"` → `pending`

**Additive Feature:**
- `"Map new UCs to components"` → `in_progress`
- One task per new UC (e.g., `"UC-5: Information flow & contracts"`) — created after mapping
- `"Test coverage for new flows"` → `pending`
- `"Wrap Up: Save progress"` → `pending`
- `"Wrap Up: Review (arch-reviewer)"` → `pending`
- `"Wrap Up: Record open items & commit"` → `pending`

### Dynamic Sub-Task Examples

**Phase 2** — after identifying dependencies:
- `"Phase 2: Clarify Auth Provider"`
- `"Phase 2: Clarify Payment Gateway"`
- `"Phase 2: Clarify Email Service"`

**Phase 3** — after identifying components:
- `"Phase 3: Component A — deep dive"`
- `"Phase 3: Component B — deep dive"`
- `"Phase 3: Component C — deep dive"`

**Phase 4** — after identifying test tiers:
- `"Phase 4: Unit test tools"`
- `"Phase 4: Integration test tools"`
- `"Phase 4: E2E test tools"`

## Step 0: Explore the Codebase

Explore the codebase to ground the architecture in reality — existing project structure, naming conventions, dependencies, build setup, and test configuration. Reference what you find during the interview.

If a codebase already exists, record the detected technology stack and confirm with the user.

Mark "Explore codebase" as `completed`.

## Navigation

The architecture covers four areas. In **First Design** mode, start with Technology Stack and follow the guided sequence. In **Iteration** mode, start wherever the user wants.

The user controls all transitions. After completing work on any topic, present a status table showing each area's progress. When an area has unreviewed content, suggest a review — but let the user decide.

## Additive Feature Path

When Impact Assessment determines that new UCs fit within the existing architecture, follow this lighter path instead of the full phase sequence.

### Step 1: Map New UCs to Components

For each new UC, identify which existing components are involved. Present the mapping as a table:

| New UC | Components | Notes |
|--------|-----------|-------|
| UC-N | Component A, Component B | Similar to UC-X pattern |

Confirm the mapping with the user.

### Step 2: Per-UC Deep Dive

For each new UC, add to the existing architecture:

1. **Information Flow** — sequence diagram showing how the UC flows through the mapped components. Follow the same format used for existing UCs in the arch file.
2. **Interface Contracts** — new operations or extensions to existing contracts needed to support the UC. Reference existing contracts where the pattern is reused.

If the Domain Model needs new terms or refinements, use the same **Domain Model Modifications** procedure from Phase 3.

### Step 3: Test Coverage

Review the test strategy for new flows:
- Are existing test tiers sufficient?
- Do the new UCs require additional integration or E2E test cases?
- Record any additions in the Test Strategy section.

### Step 4: Wrap Up

Follow the standard **Wrapping Up** procedure — increment revision, update session history, suggest next step.

## Phase 1: Technology Stack

Select the language, framework, platform, and key libraries. For each choice, record the rationale.

When a technology choice is lightweight — discuss inline and record with brief rationale.
When a technology choice is heavy (multiple viable options with significant trade-offs) — ask the user: "This seems like a decision worth investigating more deeply. Would you like to use `/think:spark-decide` to evaluate options?"

If a codebase already exists, detect the stack from project files and confirm with the user.

## Phase 2: External Dependencies

Identify external systems the software depends on. For each:

1. **Scan UCs for external interactions** — any UC that references sending notifications, authentication via third-party, file storage, external data sources, etc.
2. **Present the list** to the user with Used By (UC references), Purpose, and ask for confirmation.
3. **For each confirmed dependency**, clarify:
   - What does the system send/receive? (Access Pattern)
   - Are there constraints? (rate limits, pricing tiers, specific provider)
   - What happens if the external system is unavailable? (Fallback)
4. **Record** in the output file's External Dependencies section.

## Phase 3: Component Design

Design system architecture using the UCs and Domain Model. Read **`${CLAUDE_SKILL_DIR}/references/architecture-guide.md`** for the detailed procedure covering:

- **Component Identification** — propose components, confirm responsibilities
- **Per-Component Deep Dive** — DB schema (if data store), information flow (sequence diagrams per UC), interface contracts (operation name, direction, request/response schema)

Use the Domain Model from the usecase file as the shared vocabulary. Component names, schema fields, and contract parameters should use Domain Model terms.

### Domain Model Modifications

During component design, you may discover that the Domain Model needs changes — a concept should be split, a missing state identified, a relationship refined, or a new concept added. When this happens:

1. **Discuss with the user** — present the finding and proposed change.
2. **Spawn a `domain-updater` agent** with the usecase file path and the structured change request:

   ```
   Agent(subagent_type: "domain-updater", prompt: """
   Usecase file: <absolute path to .usecase.md>
   Changes:
   - Section: Glossary, Action: add, Content: { Concept: "Sidechain Request", Definition: "...", Key Attributes: "...", Related UCs: "UC-3, UC-9" }, Reason: "Discovered during component design — needed to distinguish sidechain SDK calls from regular session calls"
   """)
   ```

3. **On success** — the agent returns the new revision and SHA. Update the arch frontmatter `sources` SHA with the returned value. Record the change in the arch file's Upstream Changes section:

   | Source File | Section | Change | Reason |
   |------------|---------|--------|--------|
   | `<slug>.usecase.md` | Domain Model / Glossary | Added "Sidechain Request" concept | Discovered during component design — needed to distinguish sidechain SDK calls from regular session calls |

4. **On failure** — report the error to the user and decide how to proceed.

This keeps the Domain Model as the single source of truth in the usecase file while allowing architecture work to refine it without switching skills.

## Phase 4: Test Strategy

Select test tools for each tier based on the technology stack. Read **`${CLAUDE_SKILL_DIR}/references/test-strategy-guide.md`** for the detailed procedure.

1. **Identify test tiers** needed for this architecture:
   - **Unit** — component-internal logic
   - **Integration** — component boundaries, host environment APIs
   - **E2E** — full user interaction path through the UI

2. **Select tools per tier** — based on app type and technology stack:

   | App Type | Unit | Integration | E2E |
   |----------|------|-------------|-----|
   | Web app (React/Next.js) | Vitest / Jest | Playwright | Playwright |
   | VS Code Extension | Vitest | @vscode/test-electron | WebdriverIO + wdio-vscode-service |
   | Electron | Vitest / Jest | Playwright electron.launch() | Playwright |
   | API service | Vitest / Jest / pytest | supertest / httpx | Playwright CLI / curl |
   | CLI tool | Vitest / Jest / pytest | — | Bash execution |
   | Mobile (React Native) | Jest | Detox | Detox |

3. **Verify tool choices** — for each selected tool, use Technical Claim Verification to confirm compatibility with the technology stack.
4. **Record** in the output file's Test Strategy section with rationale per tier.

## Technical Claim Verification

When writing or confirming any technical statement (API support, library capabilities, framework constraints, compatibility), verify it before recording. Keep this lightweight — don't verify obvious facts, focus on claims that would cause implementation failures if wrong.

### Procedure

1. **Check the codebase first** — if the claim is about the current project's tech stack, verify by reading the actual code, configs, or dependency files.
2. **Launch an api-researcher agent** — if the claim requires external verification, spawn a background `Agent(subagent_type: "api-researcher")` with `run_in_background: true`. Prompt it with the specific claim and ask it to verify against official documentation. The agent uses `chub` first, then falls back to `WebSearch`/`WebFetch`.
3. **Continue the interview** — keep working while waiting. **Do not transition to the next phase** until all pending research results have been received and reflected.
4. **When notified** — the subagent writes results to `A4/<topic-slug>.arch.research-<label>.md` per `${CLAUDE_SKILL_DIR}/references/research-report.md`. Update the research index (`A4/<topic-slug>.arch.research-index.md`).
5. **Reflect the result** — apply the verification outcome. Add an inline reference where the claim is recorded (e.g., `(ref: research-webdriverio-vscode.md)`).
6. **Flag uncertainty** — if official documentation is ambiguous, tell the user and ask whether to proceed as assumption or investigate further.

### Research Index

Maintain `A4/<topic-slug>.arch.research-index.md` as a lookup table. Check it before launching new research to avoid duplicates.

## Progressive File Writing

### Working File Path

- Default: `A4/<topic-slug>.arch.md`
- If the file already exists → **Iteration** mode
- Tell the user the file path

### Source Revision Tracking

On **First Design**, record each source usecase file's current revision and SHA in frontmatter `sources`. On **Iteration Mode entry**, compare and update.

### How to Update

- **Track confirmed items via tasks** — after each component, dependency, or contract is confirmed, create/update a task and mark it completed.
- **Write at checkpoints only** — when a checkpoint trigger fires, use the Write tool to update the file.
- **Preserve all previously confirmed content.**

### Checkpoint Triggers

| Trigger | When |
|---------|------|
| Item count | Every 3 confirmed items within an area |
| Area transition | Moving between Technology Stack → External Dependencies → Component Design → Test Strategy. **Increment `revision`** if content changed. |
| Before review | Before launching an `arch-reviewer` subagent |
| Navigation status | When presenting the area status table |
| Session end | End iteration or finalize |

## Revision and Session History

Increment `revision` and update `revised` when: before launching a reviewer subagent, reflecting source usecase changes, reflecting review/bootstrap findings, area transition with content changes, or closing the session. Routine updates during the interview do not increment revision.

Session history is stored in `<topic-slug>.arch.history.md`. See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the format.

## Review

Reviews are handled by launching a fresh `Agent(subagent_type: "arch-reviewer")`. Suggest a review when all areas are substantially complete, before finalizing, or after significant iteration changes — but let the user decide.

Pass arch file path, usecase file path, report output path per `${CLAUDE_SKILL_DIR}/references/review-report.md`, and any previous review report paths.

## Agent Usage

Always spawn fresh subagents — context is passed via file paths, not agent memory.

- **`arch-reviewer`** — launch via `Agent(subagent_type: "arch-reviewer")`. Context passed via file paths.
- **`domain-updater`** — launch via `Agent(subagent_type: "domain-updater")`. Pass usecase file path and structured change request. Returns new revision and SHA.

## Wrapping Up

The architecture ends only when the user says so. Never conclude on your own.

When the user indicates they're done, proceed to **End Iteration**.

For the full step-by-step checklist, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`**.

### Next Step

After the architecture is finalized, suggest the next pipeline step:

> The architecture is ready. The next step is `auto-bootstrap` to set up the dev environment (project structure, dependencies, test infrastructure) and verify everything builds and runs before planning implementation.
>
> Run: `/think:auto-bootstrap <slug>`

### Output Format

Follow the Architecture template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure.
