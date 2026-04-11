---
name: think-code
description: "This skill should be used when the user needs to execute an implementation plan — autonomously implementing code unit by unit from an .impl-plan.md file. Common triggers include: 'implement the plan', 'code this plan', 'execute the plan', 'start coding', 'build from the plan', 'implement IU-1', 'continue implementation', 'resume coding'. Also applicable when a finalized impl-plan needs to be turned into working code."
argument-hint: <path to .impl-plan.md file>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskList
---

# Implementation Executor

Takes an implementation plan (from think-plan) and executes it — implementing code unit by unit through `code-executor` agents. This skill is an **orchestrator**: it manages execution order, tracks progress, and delegates actual implementation to agents. It does not write application code itself.

## Step 0: Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file.

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve in order:

1. **Full path** — use directly if the file exists
2. **Partial match** — glob for `A4/*<argument>*.impl-plan.md`
3. **Fallback** — if `A4/` does not exist, glob for `**/*<argument>*.impl-plan.md` from the project root
4. **Multiple matches** — present the candidates and ask the user to pick
5. **No match** — inform the user and ask for a different term

After resolution, present the resolved file and ask the user to confirm before reading.

## Step 1: Mode Detection

After reading the plan, scan all IU statuses:

- **All `TODO`** → Fresh Start mode
- **Mix of `DONE` and `TODO`** → Resume mode. Follow `${CLAUDE_SKILL_DIR}/references/session-resume.md`.
- **`IN_PROGRESS` found** → previous session was interrupted. Follow `${CLAUDE_SKILL_DIR}/references/session-resume.md`.

## Step 2: Codebase Exploration

Explore the project to understand structure, conventions, patterns, test setup, and build configuration. The **test framework, runner command, and report format** are critical — identify them explicitly. This context is passed to every `code-executor` agent.

## Step 3: Plan Review

Present a summary of the plan (unit counts by status, current phase, next unit, test runner) and wait for user confirmation before proceeding.

## Step 4: Orchestration Loop

Execute the plan **phase by phase**, following the Implementation Order table in the plan.

### Sequential Phase (single unit)

For each unit in the phase:

1. Create tasks in TaskList:
   - `"IU-N: spawn agent"` → set to `in_progress`
   - `"IU-N: update plan file"` → set to `pending` (blocked by spawn task)

2. Mark the IU as `IN_PROGRESS` in the plan file (via Edit tool).

3. Spawn a **fresh** `Agent(subagent_type: "code-executor")` with:
   - The IU section from the plan (description, file mappings, test strategy, acceptance criteria)
   - Codebase context from Step 0 (project structure, conventions, test framework/runner command)
   - Completion notes from the last 2-3 completed IUs (for context on prior decisions)
   - **Shared Integration Points** — if the plan has a Shared Integration Points table, include the rows for every file this IU touches. This tells the agent how its modifications fit into the overall integration pattern.

   Each IU gets a fresh agent — no reuse across units. Prior decisions are communicated via completion notes in the prompt, not via agent memory.

4. When the agent returns:
   - **On success:** mark spawn task completed. Execute the plan update task:
     - Set `**Status:** DONE` in the plan file
     - Write the agent's completion note to `**Completion Note:**`
     - Use Edit tool for surgical updates — never rewrite the entire file
   - **On deviation:** follow the Deviation Handling procedure below.

5. Move to the next unit or phase.

### Parallel Phase (multiple units)

When the Implementation Order table shows units in the same phase as parallelizable:

Read `${CLAUDE_SKILL_DIR}/references/parallel-execution.md` and follow the full procedure.

Summary:
1. Create tasks for each unit (spawn + update plan)
2. Spawn one `Agent(subagent_type: "code-executor", isolation: "worktree")` per unit
3. All agents work independently in isolated worktrees
4. After all agents complete: merge worktrees, run full test suite, update plan file

## Deviation Handling

When an agent reports a major deviation (plan vs reality mismatch):

1. Present the deviation (issue + impact) to the user.

2. Write `**Deviation Note:**` to the plan file with issue, impact, and the user's decision.

3. Reset the IU's Status to `TODO` (retryable after plan revision).

4. **Propagate block**: walk the dependency graph from the deviated unit forward. Mark all downstream IUs as `BLOCKED` in TaskList. This is runtime-only — do not persist BLOCKED in the plan file.

5. IUs with no dependency on the deviated unit continue unaffected.

Build errors and unit test failures are the agent's responsibility — only plan-reality mismatches are reported as deviations.

## Orchestrator → Agent Contract

**Input (prompt):**
- IU section: description, file mappings, test strategy, acceptance criteria
- Codebase context: project structure, conventions, test framework/runner command
- Recent completion notes from prior IUs
- Shared Integration Points rows for files this IU touches (if the plan has this section)

**Output (agent result):**
- `status`: `success` | `deviation`
- `completion_note`: bulleted text (if success)
- `commit`: git hash (if success)
- `deviation`: issue, reality, impact (if deviation)

## TaskList Usage

TaskList is the session-scoped work queue. Create tasks per IU (spawn + update plan), update on completion/deviation. Cross-session state lives in the plan file's Status fields.

## Session Management

The user can pause at any phase boundary. Progress is preserved in the plan file — completed units stay `DONE`, in-progress units are marked, and completion/deviation notes are written.

After each phase, show status (completed units, next phase) and ask to continue.

## Wrapping Up

When all units are done or the user pauses, present a summary (completed, remaining, blocked counts). The user decides when to stop. Never conclude on your own.

