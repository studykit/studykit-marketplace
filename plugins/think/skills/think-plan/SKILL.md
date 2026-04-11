---
name: think-plan
description: "This skill should be used when the user needs to create or iterate on an implementation plan from a specification — breaking down a spec into ordered, testable implementation units with dependencies, file mappings, and test strategies. Common triggers include: 'plan', 'implementation plan', 'plan the implementation', 'break down the spec', 'what should I build first', 'implementation order', 'create an impl plan', 'how to implement this spec'. Also applicable when a finalized spec needs to be turned into an actionable development roadmap."
argument-hint: <path to .arch.md file, or existing .impl-plan.md file for iteration>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Plan Builder

Takes an architecture document (from think-arch) and builds an implementation plan — ordered, testable implementation units with dependencies, file mappings, and test strategies — through collaborative dialogue. The scaffold report (from auto-scaffold) provides verified build/test/launch commands.

## Modes

This skill operates in two modes:

### First Design

Full planning sequence from Step 0 through Step 7. Applies when:
- No existing `.impl-plan.md` (new plan)
- Existing plan requires redesign (determined during Existing Plan Entry)

In the redesign case, the existing plan is retained as a reference but the planning process starts fresh from Step 0.

### Iteration

Partial updates to an existing plan. No fixed order — enter from wherever the change is needed.

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
2. **Partial match** — glob for `A4/*<argument>*.arch.md` and `A4/*<argument>*.impl-plan.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading.

**Mode detection:**
- If no existing `.impl-plan.md` → **First Design** mode. Proceed to Step 0.
- If an existing `.impl-plan.md` is found → read the plan and its source arch, then run the **Existing Plan Entry** procedure to determine the mode.

After reading, list the spec overview and any existing plan content found, then confirm with the user before proceeding.

## Existing Plan Entry

When an existing `.impl-plan.md` is found, perform these checks to assess the current state and determine the mode.

### 1. Source Arch Change Detection

Compare the stored `sha` in plan frontmatter against the current file:

1. Run `git hash-object <arch-file-path>` to get the current SHA.
2. If SHA matches the frontmatter `sha` → no arch changes.
3. If SHA differs → run `git diff <stored-sha> <current-sha> -- <arch-file-path>` to see what changed. Present the changes to the user.

### 2. Unreflected Reports

Check for report files not listed in the plan's `reflected_files`:

- `A4/<topic-slug>.impl-plan.review-*.md` (review reports)
- `A4/<topic-slug>.integration-report.r*.md` (integration reports)
- `A4/<topic-slug>.scaffold.md` (scaffold reports — check if arch source SHA differs from plan's, indicating scaffold was re-run)

Read each unreflected report and extract unaddressed issues. For integration reports, prioritize issues where `Stage` is **plan**.

After reflecting changes from an integration report, add each handled integration report filename to `reflected_files`. If the working file content changed, **increment `revision`** and update `revised` timestamp per `${CLAUDE_SKILL_DIR}/references/revision-rules.md`.

### 3. Codebase Change Check (User Option)

Ask the user: "Would you also like to check for codebase changes against the plan's file mappings?"

If yes:
- Check whether files listed in the plan's file mappings have been created, modified, or deleted since the plan's last revision.
- Present findings to the user.

### 4. Mode Determination

Based on the arch diff, assess the scope of change:

- **Iteration** — minor arch changes (component additions/modifications, contract updates)
- **Redesign (First Design)** — major arch changes (technology stack change, architecture restructuring)

Present the judgment with rationale. The user can override. Iteration → present work backlog. Redesign → proceed to Step 0 with existing plan as reference. No arch changes → default to Iteration.

## Step 0: Explore the Codebase

Explore the codebase to ground the plan in reality — project structure, naming conventions, existing patterns, test setup, and build configuration. Reference what you find during the interview.

## Step 1: Understand the Architecture

Read the arch thoroughly and present a summary (component count, UC coverage, external dependencies, test strategy tiers). Also read the source usecase file (from arch frontmatter `sources`) for UC details, domain model, and validation/error handling. Note characteristics that shape the planning approach (heavy data model → component-first; independent features → feature-first; mix → hybrid).

### Architecture Completeness Check

Before proceeding to planning, verify the architecture has sufficient detail:
- **Technology Stack** — filled with at least language and framework
- **Test Strategy** — filled with at least unit tier
- **Components** — at least one component with interface contracts
- **Information Flows** — UCs that involve multiple components should have sequence diagrams

If critical gaps exist, inform the user: "The architecture is missing [X]. Planning without this will force the implementation to guess. Would you like to address this in think-arch first, or proceed with the current state?" Let the user decide.

## Step 2: Strategy Selection

Present the implementation strategy options to the user. Read **`${CLAUDE_SKILL_DIR}/references/planning-guide.md`** → "Unit Derivation Strategy" for the detailed options.

Propose a recommendation based on the spec analysis with rationale.

## Step 3: Unit Derivation

Work through the spec systematically to identify implementation units. For each: present the unit (name, FRs, components), check sizing per `${CLAUDE_SKILL_DIR}/references/planning-guide.md` → "Unit Sizing Guidelines", clarify scope, draft, and confirm. Track confirmed units via tasks. Show progress every 2-3 units.

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

Fill the **Launch & Verify** section. If a scaffold report exists (`A4/<topic-slug>.scaffold.md`), read it and use the **Verified Commands** directly — these are confirmed working commands, not auto-detected guesses. Map them to the Launch & Verify fields:

| Scaffold Report Field | Launch & Verify Field |
|----------------------|----------------------|
| Build command (PASS) | Build command |
| Run command (PASS) | Launch command |
| Test commands (per tier) | Test runner commands |
| App type (from Environment) | App type |

If no scaffold report exists, fall back to auto-detection using findings from Step 0 and the arch's Technology Stack. Read **`${CLAUDE_SKILL_DIR}/references/planning-guide.md`** → "Launch & Verify Derivation" for the auto-detection procedure.

Present the values to the user for confirmation.

## Step 7: Risk Assessment

After all units are detailed, launch a risk assessment:

1. **Pre-assessment checkpoint** — write all pending confirmed content to the working file.
2. **Launch a `risk-assessor` subagent** — pass the plan file path, spec file path, and report output path per `${CLAUDE_SKILL_DIR}/references/risk-report.md`. If a previous risk report exists, include its path so the assessor can check whether prior risks have been addressed.
3. **Walk through the report** with the user. For each risk, the user can accept the mitigation, modify it, or dismiss the risk.
4. **If any risks are accepted or modified:** write the confirmed risks to the **Risk Assessment** section as a summary table. Add the risk report filename to `reflected_files`. Increment `revision` and update `revised` per `${CLAUDE_SKILL_DIR}/references/revision-rules.md`.
5. **If all risks are dismissed:** add the risk report filename to `reflected_files`. Increment `revision` and update `revised`. The Risk Assessment section is not added — the revision with only a `reflected_files` update signals that the report was reviewed and dismissed.

## Navigation

The user controls all transitions. After completing work on any topic, present a status table for all steps.

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/<topic-slug>.impl-plan.md`
- If the file already exists, this is **Iteration** mode — read the existing file and continue from where it left off
- Ask the user only if they want a different location

Tell the user the file path so they can follow along: "I've started a working file at `<path>`. It will update as we go."

### Source Revision Tracking

On **First Design**, record the source spec file's current revision and SHA (`git hash-object`) in plan frontmatter `sources`. On **Iteration Mode entry**, compare and update as described above.

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

Reviews are handled by launching a `plan-reviewer` subagent. Suggest a review when all units are detailed, before finalizing, or after significant iteration changes — but let the user decide.

Launch with `Agent(subagent_type: "plan-reviewer")`, providing plan file path, spec file path, report output path per `${CLAUDE_SKILL_DIR}/references/review-report.md`, and any previous review report paths. Walk through flagged issues with the user.

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

