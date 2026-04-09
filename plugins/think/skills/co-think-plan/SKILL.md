---
name: co-think-plan
description: "This skill should be used when the user needs to create or iterate on an implementation plan from a specification — breaking down a spec into ordered, testable implementation units with dependencies, file mappings, and test strategies. Common triggers include: 'plan', 'implementation plan', 'plan the implementation', 'break down the spec', 'what should I build first', 'implementation order', 'create an impl plan', 'how to implement this spec'. Also applicable when a finalized spec needs to be turned into an actionable development roadmap."
argument-hint: <path to .spec.md file, or existing .impl-plan.md file for iteration>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Plan Builder

Takes a specification (from co-think-spec) and builds an implementation plan — ordered, testable implementation units with dependencies, file mappings, and test strategies — through collaborative dialogue.

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

**Impact propagation rule:** when something changes in one unit, check whether it affects other units:
- Unit split → do dependencies need updating? Does the order change?
- FR added to a unit → does the test strategy cover it? Does the file mapping need new entries?
- Dependency change → does the implementation order still hold?

Always surface these cross-unit impacts to the user rather than silently assuming they're fine.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve them by searching `A4/co-think/`:

1. **Full path** — use directly
2. **Partial match** — glob for `A4/co-think/*<argument>*.spec.md` and `A4/co-think/*<argument>*.impl-plan.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

After resolution, present the resolved file(s) and ask the user to confirm before reading:

> **Resolved input files:**
> - `A4/co-think/agent-orchestrator.spec.md`
>
> Proceed with these files?

**Mode detection:**
- If the target `.impl-plan.md` file already exists → **Iteration** mode. Read the plan file and its source spec.
- If only a spec file is found (no existing plan) → **First Design** mode.

**Iteration Mode entry:** When entering Iteration mode, check two things:

1. **Source spec changes** — compare the stored `sha` in plan frontmatter against the current file:
   - Run `git hash-object <spec-file-path>` to get the current SHA.
   - If SHA matches → no changes, skip.
   - If SHA differs → run `git diff <stored-sha> <current-sha>` to see exactly what changed.
   - Present the changes to the user: "The source spec has been updated. Changes: [list]. Review these changes before continuing?"
   - Walk through each change with the user to determine plan impact (new units needed, existing units to update, dependency changes).
   - After reflecting, update `sources` in plan frontmatter (both `revision` and `sha`).

2. **Unreflected review reports** — check for `A4/co-think/<topic-slug>.impl-plan.review-*.md` files against `reflected_files` in frontmatter:
   - Read each unreflected review report and extract issues that were not yet addressed.
   - Present unreflected findings to the user alongside the Open Items from the last revision.

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

After each unit is confirmed, write it to the output file immediately.

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
4. **Risk assessment** — any risks specific to this unit.

After each unit's details are confirmed, update the output file.

## Step 6: Risk Assessment

After all units are detailed, review cross-cutting risks:

- **Complex integrations** — units that depend on external services
- **Schema migrations** — units that modify existing database schemas
- **Performance-sensitive areas** — units with NFR constraints
- **Unknowns** — areas where the spec has Open Items

Present risks and ask the user for mitigation strategies or acceptance.

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
> | Risk Assessment | Not started |
>
> What would you like to work on next?

## Progressive File Writing

### Working File Path

At the start of the session, determine the file path:
- Default: `A4/co-think/<topic-slug>.impl-plan.md`
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

- **Use the Write tool** to rewrite the entire file each time. This keeps the file consistent and avoids partial edit issues.
- **Preserve all previously confirmed content** — never remove or reorder confirmed units.
- After each unit is confirmed, update the Implementation Units section.
- After dependency mapping, add the Dependency Graph section.
- After each detail pass, update the unit with file mappings, tests, and criteria.
- Show progress: "That's 4 units defined, 2 fully detailed. Let's continue."

## Revision and Session History

Increment `revision` in frontmatter and update `revised` timestamp when reflecting external input (review findings) or closing the session. Routine updates during the interview (unit confirmation, detail additions) do not increment revision.

Session history is stored in a separate file (`<topic-slug>.impl-plan.history.md`). See `${CLAUDE_SKILL_DIR}/references/session-history.md` for the full format.

At the end of each session:

1. **Scan for incomplete items** — walk through each unit and identify what's missing or underspecified:
   - Units without file mappings
   - Units without test strategies
   - Units with vague acceptance criteria
   - Missing dependency declarations
2. **Append a Session Close entry** to the history file per `${CLAUDE_SKILL_DIR}/references/session-history.md`.
3. **Update the working file** — update the Open Items and Next Steps sections. **Increment `revision`** and update `revised` timestamp.

### Iteration Mode Entry

When entering **Iteration** mode:
1. Read the working file — Open Items and Next Steps show the current backlog.
2. Present the Open Items table as a **work backlog**:

   > Here are the open items from the last session:
   >
   > | # | Section | Item | What's Missing |
   > |---|---------|------|---------------|
   > | 1 | IU-3 | Test Strategy | No test scenarios defined |
   > | 2 | IU-5 | File Mapping | Paths not specified |
   > | ...
   >
   > Which item would you like to work on first? Or would you like to focus on something else?

3. Let the user choose — they may pick from the backlog or bring new topics.

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

Subagents are launched with a `name` for potential reuse within the session. On subsequent invocations of the same agent type, offer the user a choice between reusing the existing agent or spawning a fresh one.

For the full reuse pattern, see **`${CLAUDE_PLUGIN_ROOT}/references/agent-reuse-guide.md`**.

- **`plan-reviewer`** — first launch via `Agent(subagent_type: "plan-reviewer", name: "plan-reviewer")`. Context passed via file paths.

## Wrapping Up

The plan ends only when the user says so. Never conclude on your own.

When the user indicates they're done, ask whether they want to:
- **End this iteration** (come back later to refine further)
- **Finalize** (mark as ready for implementation)

For the full step-by-step checklists, read **`${CLAUDE_SKILL_DIR}/references/session-procedures.md`**.

### Output Format

Follow the Implementation Plan template in `${CLAUDE_SKILL_DIR}/references/output-template.md` for the final file structure.

## Facilitation Guidelines

- **One question at a time.** Don't overwhelm with multiple decisions.
- **Stay concrete.** Anchor to specific FRs and components, not abstract patterns.
- **Use the spec's language.** Reference FR IDs, component names, and domain terms from the spec.
- **Challenge assumptions.** If the user proposes an order, check dependencies. If a unit seems too large, suggest splitting.
- **Show the impact.** When something changes, trace the effect on dependencies, tests, and ordering.
- **Every 2-3 units:** Brief progress snapshot.
