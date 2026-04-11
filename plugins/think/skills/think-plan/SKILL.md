---
name: think-plan
description: "This skill should be used when the user needs to create or iterate on an implementation plan from a specification — breaking down a spec into ordered, testable implementation units with dependencies, file mappings, and test strategies. Common triggers include: 'plan', 'implementation plan', 'plan the implementation', 'break down the spec', 'what should I build first', 'implementation order', 'create an impl plan', 'how to implement this spec'. Also applicable when a finalized spec needs to be turned into an actionable development roadmap."
argument-hint: <path to .spec.md file, or existing .impl-plan.md file for iteration>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Plan Builder

Takes a specification (from think-spec) and builds an implementation plan — ordered, testable implementation units with dependencies, file mappings, and test strategies — through collaborative dialogue.

## Modes

This skill operates in two modes, determined by the input:

### First Design

Input is a spec file (no existing `.impl-plan.md`). Follows a guided sequence:

1. **Codebase Exploration** — understand the existing project structure and conventions
2. **Strategy Selection** — choose an implementation approach (component-first, feature-first, hybrid)
3. **Unit Derivation** — break the spec into implementation units
4. **Dependency Mapping** — establish ordering and parallelism
5. **Detail Pass** — fill in file mappings, test strategies, acceptance criteria per unit

### Iteration

Input is an existing `.impl-plan.md` file. No fixed order — enter from wherever the change is needed.

**Entry procedure:** Read `${CLAUDE_SKILL_DIR}/references/iteration-entry.md` and follow the checks before starting work.

**Impact propagation rule:** when something changes in one unit, check whether it affects other units:
- Unit split → do dependencies need updating? Does the order change?
- FR added to a unit → does the test strategy cover it? Does the file mapping need new entries?
- Dependency change → does the implementation order still hold?

Always surface these cross-unit impacts to the user rather than silently assuming they're fine.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/`:

1. **Full path** — use directly
2. **Partial match** — glob for `A4/*<argument>*.spec.md` and `A4/*<argument>*.impl-plan.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/agent-orchestrator.spec.md`
>
> Proceed with these files?

**Mode detection:**
- If the target `.impl-plan.md` file already exists → **Iteration** mode. Read the plan file and its source spec, then follow `${CLAUDE_SKILL_DIR}/references/iteration-entry.md`.
- If only a spec file is found (no existing plan) → **First Design** mode.

After reading, list the spec overview and any existing plan content found, then confirm with the user before proceeding.

## Step 0: Explore the Codebase

Before starting, explore the current codebase to understand:

- **Project structure** — directories, key files, existing source layout
- **Naming conventions** — how files and directories are named (kebab-case, camelCase, etc.)
- **Existing patterns** — how similar features are structured (controllers, services, models, etc.)
- **Test setup** — testing framework, test file locations, test naming conventions
- **Build configuration** — package manager, build tool, existing scripts

This grounds the implementation plan in reality. Reference what you find during the interview — e.g., "I see existing services follow a `src/services/<name>.service.ts` pattern. Should we follow that?"

## Step 1: Understand the Spec

Read the spec thoroughly and present a summary:

> **Spec Summary:**
> - **FRs:** 8 total (5 UI, 3 Non-UI)
> - **Components:** 4 (AuthService, UserStore, NotificationService, WebUI)
> - **Domain concepts:** 6
> - **External dependencies:** 2 (OAuth Provider, Email Service)
>
> Ready to start planning?

Note any spec characteristics that shape the planning approach:
- Heavy data model → consider component-first (bottom-up)
- Independent features → consider feature-first (vertical slices)
- Mix of foundation + features → consider hybrid

## Step 2: Strategy Selection

Present the implementation strategy options to the user. Read **`${CLAUDE_SKILL_DIR}/references/planning-guide.md`** → "Unit Derivation Strategy" for the detailed options.

Propose a recommendation based on the spec analysis:

> Based on the spec, I recommend a **hybrid** approach:
> 1. Foundation units first (DB schemas, shared utilities)
> 2. Then vertical feature slices
>
> Rationale: The spec has a clear data model that multiple features depend on, so building the foundation first avoids rework.
>
> Does this approach work for you?

## Step 3: Unit Derivation

Work through the spec systematically to identify implementation units. For each proposed unit:

1. **Present the unit** — name, FRs covered, components involved.
2. **Check sizing** — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` → "Unit Sizing Guidelines". If too large, propose splitting. If too small, propose merging.
3. **Ask clarifying questions** — one at a time — about scope, boundaries, and priorities.
4. **Draft the unit** and present it for confirmation.
5. Move to the next unit only when the user confirms.

After each unit is confirmed, track it via a task (e.g., `IU-1: <title>`, marked completed). The file is written at checkpoints — not after every unit (see Progressive File Writing).

### Progress Snapshots

Every 2-3 units, show progress:

> **Progress:**
> - IU-1: User data model and schema (FR-1, FR-2) — confirmed
> - IU-2: Authentication service (FR-3, FR-4) — confirmed
> - IU-3: [working on it]
>
> FRs covered: 4/8 | Components covered: 2/4

## Step 4: Dependency Mapping

After all units are defined:

1. **Analyze dependencies** — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` → "Dependency Analysis" for the procedure.
2. **Present the dependency graph** — show which units depend on which.
3. **Propose implementation order** — based on dependencies and parallelism opportunities.
4. **Confirm with user** — they may have preferences about priority or ordering.

Generate the PlantUML dependency graph and the Implementation Order table.

## Step 5: Detail Pass

For each confirmed unit, fill in the remaining details. Work through units in implementation order:

1. **File mapping** — specific file paths and change descriptions. Reference codebase conventions from Step 0.
2. **Test strategy** — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` → "Test Strategy Selection" for guidance. Derive test scenarios from the FRs.
3. **Acceptance criteria** — measurable criteria derived from FR behavior steps.

After each unit's details are confirmed, track completion via a task update. The file is updated at the next checkpoint.

## Step 6: Launch & Verify

Fill the **Launch & Verify** section using findings from Step 0 (Codebase Exploration) and the spec's Technology Stack. Read **`${CLAUDE_SKILL_DIR}/references/planning-guide.md`** → "Launch & Verify Derivation" for the auto-detection procedure.

Present the detected values to the user for confirmation:

> **Launch & Verify:**
> - App type: VS Code Extension
> - Build: `npm run compile`
> - Launch: `code --extensionDevelopmentPath=.`
> - View: "Visual Claude" webview panel
> - Verify tool: WebdriverIO + wdio-vscode-service
> - Smoke: "open the panel and send a message"
>
> Does this look right?

If any value cannot be auto-detected, ask the user.

## Step 7: Risk Assessment

After all units are detailed, launch a risk assessment:

1. **Pre-assessment checkpoint** — write all pending confirmed content to the working file.
2. **Launch a `risk-assessor` subagent** — pass the plan file path, spec file path, and report output path per `${CLAUDE_SKILL_DIR}/references/risk-report.md`. If a previous risk report exists, include its path so the assessor can check whether prior risks have been addressed.
3. **Walk through the report** with the user. For each risk, the user can accept the mitigation, modify it, or dismiss the risk.
4. **If any risks are accepted or modified:** write the confirmed risks to the **Risk Assessment** section as a summary table. Add the risk report filename to `reflected_files`. Increment `revision` and update `revised` per `${CLAUDE_SKILL_DIR}/references/revision-rules.md`.
5. **If all risks are dismissed:** add the risk report filename to `reflected_files`. Increment `revision` and update `revised`. The Risk Assessment section is not added — the revision with only a `reflected_files` update signals that the report was reviewed and dismissed.

## Navigation

The user controls all transitions. After completing work on any topic, present the current status:

> Here's where we are:
>
> | Step | Status |
> |------|--------|
> | Codebase Exploration | Done |
> | Strategy Selection | Hybrid approach |
> | Unit Derivation | 6/6 units defined |
> | Dependency Mapping | Done |
> | Detail Pass | 4/6 units detailed |
> | Launch & Verify | Done |
> | Risk Assessment | Not started |
>
> What would you like to work on next?

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/<topic-slug>.impl-plan.md`
- If the file already exists, this is **Iteration** mode — read the existing file and continue from where it left off
- Ask the user only if they want a different location

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### Source Revision Tracking

On **First Design**, record the source spec file's current revision in the plan frontmatter:

```yaml
sources:
  - file: <topic-slug>.spec.md
    revision: <current revision number>
    sha: <git hash-object output>
```

On **Iteration Mode entry**, compare and update as described in the Iteration Mode entry procedure above.

### How to Update

- **Track confirmed items via tasks** — after each unit is confirmed or detailed, create/update a task (e.g., `IU-1: <title>`) and mark it completed. This gives the user a running overview via TaskList without writing the file.
- **Use the Write tool** for initial file creation (skeleton with frontmatter, Overview, and Implementation Strategy).
- **Use the Edit tool** at checkpoints for subsequent updates — adding units, updating details, adding sections. This avoids rewriting the entire file and reduces the risk of accidentally dropping confirmed content.
- **Never remove or reorder confirmed units.**
- Show progress: "That's 4 units defined, 2 fully detailed. Let's continue."

### Checkpoint Triggers

| Trigger | When |
|---------|------|
| Unit count | Every 3 confirmed units during Unit Derivation |
| Step transition | Moving between steps (Unit Derivation → Dependency Mapping → Detail Pass) |
| Before review | Before launching a `plan-reviewer` subagent |
| Navigation status | When presenting the step status table to the user |
| Session end | End iteration or finalize |

## Revision and Session History

For revision increment rules, read `${CLAUDE_SKILL_DIR}/references/revision-rules.md`.

Session history is stored in a separate file (`<topic-slug>.impl-plan.history.md`). See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the full format.

## Review

Reviews are handled by launching a `plan-reviewer` subagent. Each invocation is independent — context is passed via file paths.

### Triggering a Review

Suggest a review when:
- All units are defined and detailed
- Before finalizing the plan
- After significant changes in iteration mode

Always let the user decide. Present:

> All 6 units are defined and detailed. Would you like to run a review before finalizing?

### Review Invocation

Launch with: `Agent(subagent_type: "plan-reviewer", name: "plan-reviewer")`

Provide:
- Plan file path
- Spec file path
- Report output path per `${CLAUDE_SKILL_DIR}/references/review-report.md`
- Any previous review report paths

### Post-Review

Walk through each flagged issue with the user. They can accept, modify, or defer.

## Agent Usage

Always spawn fresh subagents — context is passed via file paths, not agent memory.

- **`plan-reviewer`** — launch via `Agent(subagent_type: "plan-reviewer")`. Context passed via file paths.
- **`risk-assessor`** — launch via `Agent(subagent_type: "risk-assessor")`. Pass plan file path, spec file path, and report output path per `${CLAUDE_SKILL_DIR}/references/risk-report.md`.

## Wrapping Up

The plan ends only when the user says so. Never conclude on your own.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as ready for implementation)

For the full step-by-step checklists, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`**.

After finalizing, suggest the next step: "To start implementing this plan, run `/think:think-code <file_path>`."

### Output Format

Follow the Implementation Plan template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure.

## Facilitation Guidelines

- **One question at a time.** Don't overwhelm with multiple decisions.
- **Stay concrete.** Anchor to specific FRs and components, not abstract patterns.
- **Use the spec's language.** Reference FR IDs, component names, and domain terms from the spec.
- **Challenge assumptions.** If the user proposes an order, check dependencies. If a unit seems too large, suggest splitting.
- **Show the impact.** When something changes, trace the effect on dependencies, tests, and ordering.
- **Every 2-3 units:** Brief progress snapshot.
