---
name: think-arch
description: "This skill should be used when the user needs to design or iterate on system architecture — technology stack, component design, information flows, interface contracts, and test strategy. Common triggers include: 'architecture', 'design the system', 'component design', 'tech stack', 'how should we build this', 'system design', 'interface contracts', 'test strategy', 'what tools should we use'. Also applicable when use cases from think-usecase need to be turned into a buildable architecture."
argument-hint: <path to .usecase.md file, or existing .arch.md file for iteration>
allowed-tools: Read, Write, Agent, WebSearch, WebFetch, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Architecture Designer

Takes use cases (from think-usecase) and designs the system architecture — technology stack, external dependencies, components, information flows, interface contracts, and test strategy — through collaborative dialogue.

## Modes

- **No existing `.arch.md`** → start from Phase 1 (Technology Stack) and follow the guided sequence.
- **Existing `.arch.md`** → run Iteration Mode entry checks (feedback, source changes), then the user chooses which area to work on. They can start from Phase 1 if a fundamental rethink is needed, or jump to any specific area.

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

1. **Full path** — use directly
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
- `A4/<topic-slug>.scaffold.md` (scaffold reports — issues where `Stage: arch`)
- `A4/<topic-slug>.integration-report.r*.md` (integration reports — issues where `Stage: arch`)
- `A4/<topic-slug>.plan.md` (check for blocked status with arch-level issues)
- `A4/<topic-slug>.test-report.c*.md` (check for failures diagnosed as arch-level)

For integration reports, prioritize issues where the diagnosis stage is **arch**. For plan deviations, read the Deviation Note to determine if the root cause is an architecture assumption that doesn't hold.

### 3. Recommend Starting Point

Analyze the collected feedback and open items. Recommend which area to work on first, with rationale. The user can follow the recommendation or choose a different starting point.

## Session Task List

At the start of the session, create a task list showing the major areas so the user can track progress. Mark each area as `in_progress` when entering it and `completed` when done.

**First Design tasks:**
- `"Explore codebase"` → `in_progress`
- `"Technology Stack"` → `pending`
- `"External Dependencies"` → `pending`
- `"Component Design"` → `pending`
- `"Test Strategy"` → `pending`
- `"Wrap up"` → `pending`

**Iteration tasks** (adjust based on the work backlog):
- `"Review open items and backlog"` → `in_progress`
- `"Address selected items"` → `pending`
- `"Wrap up"` → `pending`

The user can freely navigate between areas. Update task status as areas are worked on — an area can go back to `in_progress` if revisited.

## Step 0: Explore the Codebase

Explore the codebase to ground the architecture in reality — existing project structure, naming conventions, dependencies, build setup, and test configuration. Reference what you find during the interview.

If a codebase already exists, record the detected technology stack and confirm with the user.

Mark "Explore codebase" as `completed`.

## Navigation

The architecture covers four areas. In **First Design** mode, start with Technology Stack and follow the guided sequence. In **Iteration** mode, start wherever the user wants.

The user controls all transitions. After completing work on any topic, present a status table showing each area's progress. When an area has unreviewed content, suggest a review — but let the user decide.

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
2. **Launch a research subagent** — if the claim requires external verification, spawn a background `Agent` with `run_in_background: true`. Prompt it with the specific claim and ask it to verify against official documentation using `WebSearch`/`WebFetch`.
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

Increment `revision` and update `revised` when: before launching a reviewer subagent, reflecting source usecase changes, reflecting review/scaffold findings, area transition with content changes, or closing the session. Routine updates during the interview do not increment revision.

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

### Output Format

Follow the Architecture template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure.
