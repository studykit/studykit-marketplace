---
name: think-code
description: "This skill should be used when the user needs to execute an implementation plan — autonomously implementing code unit by unit from an .impl-plan.md file. Common triggers include: 'implement the plan', 'code this plan', 'execute the plan', 'start coding', 'build from the plan', 'implement IU-1', 'continue implementation', 'resume coding'. Also applicable when a finalized impl-plan needs to be turned into working code."
version: 0.1.0
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

After resolution, present the resolved file and ask the user to confirm before reading:

> **Resolved input file:**
> - `A4/agent-orchestrator.impl-plan.md`
>
> Proceed with this file?

## Step 1: Mode Detection

After reading the plan, scan all IU statuses:

- **All `TODO`** → Fresh Start mode
- **Mix of `DONE` and `TODO`** → Resume mode. Follow `${CLAUDE_SKILL_DIR}/references/session-resume.md`.
- **`IN_PROGRESS` found** → previous session was interrupted. Follow `${CLAUDE_SKILL_DIR}/references/session-resume.md`.

## Step 2: Codebase Exploration

Before implementing anything, explore the project to understand:

- **Project structure** — directories, key files, source layout
- **Naming conventions** — how files and directories are named
- **Existing patterns** — how similar features are structured
- **Test setup** — testing framework, test runner command, test file locations, test report format
- **Build configuration** — package manager, build tool, existing scripts

The **test framework, runner command, and report format** are critical — they determine how every agent runs tests. Identify them explicitly (e.g., `npm test`, `pytest`, `./gradlew test`).

This context is passed to every `code-executor` agent.

## Step 3: Plan Review

Present a summary of the plan:

> **Plan Summary:**
> - **Units:** 6 total (2 DONE, 4 TODO)
> - **Current phase:** Phase 2
> - **Next unit:** IU-3 (Authentication Service)
> - **Test runner:** `npm test`
>
> Ready to start?

Wait for user confirmation before proceeding.

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

1. Present the deviation report to the user:

   ```
   ⚠ IU-3: Authentication Service — DEVIATION

   Issue:
     Plan specifies OAuth2 with Google provider, but existing codebase
     uses SAML for all auth flows.

   Impact:
     Cannot proceed without a design decision on auth coexistence.
   ```

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

**Output (agent result):**
- `status`: `success` | `deviation`
- `completion_note`: bulleted text (if success)
- `commit`: git hash (if success)
- `deviation`: issue, reality, impact (if deviation)

## TaskList Usage

TaskList serves as the orchestrator's **session-scoped work queue**:

- Before spawning agents for a phase, create tasks for each IU:
  - `"IU-N: spawn agent"` → `in_progress`
  - `"IU-N: update plan file"` → `pending` (blocked by spawn task)
- When agent returns: mark spawn task completed, then execute the plan update task
- On deviation: mark spawn task completed (with deviation metadata), create task `"IU-N: report deviation to user"`, and tasks marking downstream IUs as blocked
- TaskList is session-scoped — **cross-session state lives in the plan file's Status fields**

## Session Management

The user can pause at any phase boundary. Progress is preserved in the plan file — completed units stay `DONE`, in-progress units are marked, and completion/deviation notes are written.

After each phase, show status:

> **Phase 2 complete:**
> - IU-3: DONE
> - IU-4: DONE
>
> **Next:** Phase 3 (IU-5, IU-6 — parallel)
>
> Continue?

## Wrapping Up

When all units are done, or when the user pauses:

> **Implementation Summary:**
> - **Completed:** IU-1, IU-2, IU-3, IU-4 (4/6)
> - **Remaining:** IU-5 (TODO), IU-6 (TODO)
> - **Blocked:** none
>
> All completed units have passing tests and are committed.

The user decides when to stop. Never conclude on your own.

## Additional Resources

### Reference Files

For detailed procedures, consult:

- **`references/execution-procedure.md`** — Step-by-step procedure followed by each code-executor agent (read the IU, align with codebase, implement, handle deviations, write completion note)
- **`references/test-and-commit.md`** — Test execution and commit conventions for agents (test framework discovery, IU-level test requirements, commit message format)
- **`references/parallel-execution.md`** — Full parallel execution and merge procedure (worktree spawning, merge sequencing, integration test, deviation propagation)
- **`references/session-resume.md`** — Resume and interrupted session handling (context recovery, state consistency check, partial work cleanup)
