---
name: think-plan
description: "This skill should be used when the user needs to generate and execute an implementation plan from an architecture document — autonomously planning, implementing, testing, and iterating until tests pass. Common triggers include: 'plan', 'implement', 'build from arch', 'execute the architecture', 'plan and implement', 'make this work', 'plan and build'. Also applicable when a finalized architecture needs to be turned into working, tested code."
argument-hint: <path to .arch.md file, or existing .plan.md file for resume>
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Implementation Plan Builder & Executor

Takes an architecture document (from think-arch) and autonomously plans, implements, and tests the project — iterating until integration and smoke tests pass.

## Input

Resolve the input from **$ARGUMENTS** using the file resolution rules below, then read the file(s).

If no argument is provided, ask the user for a slug, filename, or path.

### File Resolution

Arguments can be full paths, partial filenames, or slugs. Resolve by searching `A4/`:

1. **Full path** — extract the slug from the filename (e.g., `A4/chat-app.arch.md` → `chat-app`), then scan for related files: `A4/*<slug>*.arch.md` and `A4/*<slug>*.plan.md`
2. **Partial match** — glob for `A4/*<argument>*.arch.md` and `A4/*<argument>*.plan.md`
3. **Multiple matches per type** — present the candidates and ask the user to pick
4. **No match** — inform the user and ask for a different term

**Mode detection:**
- If an existing `.plan.md` is found → **Resume** mode. Check frontmatter `phase` and `cycle` to determine where to continue.
- If only `.arch.md` found → **Fresh** mode. Proceed to Phase 1.

## Resume Mode

When an existing `.plan.md` is found:

1. Read plan frontmatter — extract `phase`, `cycle`, `status`, `sources`.
2. **Source change detection** — compare `sources` SHA against current files (`git hash-object`). If changed, assess scope:
   - Minor changes → resume from current phase, incorporating changes
   - Major changes (tech stack, architecture restructuring) → restart from Phase 1
3. **Bootstrap staleness** — if a bootstrap report exists, compare its source arch SHA against the current arch file. If the arch changed after the bootstrap was generated, warn the user that bootstrap commands may be outdated and suggest re-running `auto-bootstrap`.
4. **Check unreflected reports** — compare existing report files against `reflected_files`. Read any unreflected reports and reflect them before continuing.
5. Continue from the recorded phase/cycle.

---

## Phase 1 — Plan Generation + Verification

### Step 1: Read Sources

Read the `.arch.md` and `.usecase.md` thoroughly. Extract:
- Technology stack, components, interface contracts
- All UCs (IDs, actors, goals, flows, expected outcomes, validation, error handling)
- Domain model, external dependencies
- Test strategy tiers

Check for a bootstrap report (`A4/<slug>.bootstrap.md`):
- If present → read it. Extract verified build, run, and test commands. These are used directly in Launch & Verify (Step 3) instead of auto-detection. Also note any issues with `Stage: arch` — these may indicate architecture assumptions that don't hold.
- If absent → proceed without it. Suggest running `auto-bootstrap` first, but continue if the user chooses not to.

### Step 2: Explore Codebase

Explore the project to understand structure, conventions, patterns, test setup, and build configuration.

### Step 3: Generate Plan

Enter plan mode. Generate the implementation plan covering:
- Implementation strategy (component-first / feature-first / hybrid) — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` for guidance
- Implementation units with descriptions, file mappings, dependencies
- Dependency graph and implementation order
- Test plan:
  - **Test file convention** — directory structure, naming pattern, co-location rules (derive from bootstrap report or existing codebase)
  - **Integration test cases** — which component interactions to verify, scenario description, expected outcome, test file path
  - **Smoke test cases** — which UC critical paths to verify end-to-end, scenario steps, expected outcome, test file path
  - Unit test content is not specified — IU subagents decide what to test based on the code they implement
- IU file mappings must include both source files and unit test file paths (following the test file convention)
- Launch & Verify configuration — if a bootstrap report exists, use its verified commands directly for build, launch, and test runner commands; otherwise, auto-detect per planning guide

Exit plan mode. Write the plan to `A4/<slug>.plan.md` per `${CLAUDE_SKILL_DIR}/references/output-template.md`.

Record source file SHAs in frontmatter. Set `phase: plan-review`, `revision: 1`.

**Commit:** plan + history

### Step 4: Verification Loop (max 3 rounds)

For each round:

1. Spawn a `plan-reviewer` agent via `Agent(subagent_type: "think:plan-reviewer")` — pass plan file path, arch file path, usecase file path, and report output path per `${CLAUDE_SKILL_DIR}/references/review-report.md`.

   The agent checks:
   - FR coverage (every FR mapped to at least one IU)
   - Component/contract coverage
   - Tech stack consistency
   - Test plan completeness (unit → integration → smoke)
   - Dependency validity
   - File mapping specificity
   - Acceptance criteria quality

2. Agent writes report to `A4/<slug>.plan.review-r<N>.md`.

3. Read the report. Analyze each issue:
   - **Plan issues** → auto-reflect into plan. Add report to `reflected_files`. Increment `revision`. Continue to next round.
   - **Arch/usecase issues** → **stop**. Set `status: blocked`. Report to user with specific issues found. Suggest running `think-arch` or `think-usecase` to address them.

4. **Commit:** report + updated plan + history entry

After verification passes:
- Set `phase: implement`, `cycle: 1`
- **Commit:** updated plan + history entry

---

## Phase 2 — Implement + Test Loop (max 3 cycles)

Implementation is delegated to subagents on a per-IU basis. Each subagent runs in a fresh context and receives only its assigned IU details. think-plan orchestrates the execution order, tracks progress, and manages the cycle loop.

### IU Status Tracking

Each IU in `.plan.md` has a status field:

| Status | Meaning |
|--------|---------|
| `pending` | Not yet assigned |
| `implementing` | Assigned to a subagent |
| `done` | Implemented + unit tests pass |
| `failed` | Implementation or unit test failed |

think-plan updates IU statuses in `.plan.md` as subagents complete their work.

### Step 5: IU Implementation

Execute IUs following the dependency graph:

1. **Identify ready IUs** — IUs whose dependencies are all `done` and whose own status is `pending` (or `failed` in a retry cycle).
2. **Spawn subagents** — one per ready IU, using `Agent(subagent_type: "think:iu-implementer")`. Independent IUs can run in parallel.

Each subagent receives:
- The specific IU details (description, file mappings, acceptance criteria)
- Relevant interface contracts from the plan (contracts the IU consumes or provides)

```
Agent(subagent_type: "think:iu-implementer", prompt: """
IU: <IU identifier and title>
Description: <IU description from plan>
Source files: <list of source files to create/modify>
Test files: <list of unit test file paths>
Acceptance criteria: <from plan>
Interface contracts: <relevant contracts this IU consumes or provides>

Implement this IU and write unit tests. All unit tests must pass.
Commit code + unit tests.
Return: result (pass/fail), summary of changes, issues encountered.
""")
```

3. **Track progress** — as each subagent completes:
   - Pass → set IU status to `done`, identify next ready IUs, spawn their subagents
   - Fail → set IU status to `failed`, record the failure summary. Continue with other independent IUs.

4. **Checkpoint** — after every 3 completed IUs, update `.plan.md` with current statuses and commit.

### Step 6: Integration + Smoke Test

After all IUs are `done` (or after handling failures), run integration and smoke tests:

1. **Spawn a test-runner agent** via `Agent(subagent_type: "think:test-runner")` with the plan's test plan section and Launch & Verify config.
2. The agent runs integration and smoke tests, writes results to `A4/<slug>.test-report.c<N>.md` per `${CLAUDE_SKILL_DIR}/references/test-report.md`.
3. The agent records **factual results only** — no diagnosis classification.
4. **Commit:** test report

```
Agent(subagent_type: "think:test-runner", prompt: """
Plan file: <absolute path to .plan.md>

Run integration and smoke tests as defined in the plan's test plan section.
Write the test report to A4/<slug>.test-report.c<N>.md per the template
in references/test-report.md.
""")
```

### Step 7: Analyze Results

Read the test report and IU failure summaries.

**If all IUs are `done` and all integration/smoke tests pass:**
- Set `status: complete`
- **Commit:** updated plan + history entry
- Report success to user. Done.

**If there are failures** — classify each failure using the plan and arch context from Phase 1:

1. **Identify failures** — from IU failure summaries and/or the test report.
2. **Classify** — determine whether the root cause is plan, arch, or usecase:
   - **Arch/usecase issues** → **stop**. Set `status: blocked`. Report to user with specific issues and which upstream document needs updating. **Commit:** updated plan + history entry.

3. **Plan issues — autonomous plan revision:**
   a. Identify affected IUs from the failure root causes
   b. Revise affected IUs — update descriptions, file mappings, dependencies, or acceptance criteria as needed
   c. Check for ripple effects — if a revised IU is a dependency of other IUs (per dependency graph), verify those IUs still hold
   d. Reset affected IU statuses to `pending`. Dependent IUs that need re-implementation also reset to `pending`.
   e. Add test report to `reflected_files`. Increment `revision`.
   f. **Commit:** updated plan + history entry

4. **Verify revised plan** — spawn `plan-reviewer` agent with the updated plan. If the reviewer finds:
   - **Plan-level issues** → fix and re-verify (max 2 rounds within this step)
   - **Arch/usecase issues** → **stop**. Set `status: blocked`. Report to user.
   - **No issues** → increment `cycle`. Go to Step 5 (only `pending` IUs are re-implemented).

**If cycle 3 exhausted with failures:**
- Set `status: blocked`
- **Commit:** updated plan + history entry
- Report to user: current state, all test reports, IU statuses, and remaining failures.

---

## File Structure

```
A4/<slug>.plan.md              — plan
A4/<slug>.plan.history.md      — event log (append-only)
A4/<slug>.plan.review-r1.md    — Phase 1 verification report (round 1)
A4/<slug>.plan.review-r2.md    — Phase 1 verification report (round 2)
A4/<slug>.test-report.c1.md    — Phase 2 test report (cycle 1)
A4/<slug>.test-report.c2.md    — Phase 2 test report (cycle 2)
```

## Frontmatter

```yaml
---
type: plan
topic: "<topic>"
revision: 1
status: draft | verified | implementing | complete | blocked
phase: plan-review | implement | test
cycle: 1
sources:
  - file: <slug>.arch.md
    sha: <hash>
  - file: <slug>.usecase.md
    sha: <hash>
reflected_files: []
created: <YYYY-MM-DD HH:mm>
revised: <YYYY-MM-DD HH:mm>
---
```

## Revision Rules

Read `${CLAUDE_SKILL_DIR}/references/revision-rules.md` for the full rules.

Increment `revision` and update `revised` when:
1. Plan initial creation
2. Reflecting a review report (Phase 1)
3. Reflecting a test report (Phase 2)
4. Status change

## History

Append-only event log in `A4/<slug>.plan.history.md`. See `${CLAUDE_SKILL_DIR}/references/session-history.md` for format.

## Commit Points

| Event | What to commit |
|---|---|
| Plan initial creation | plan + history |
| Review reflection | report + updated plan + history |
| Verification passed | updated plan + history |
| IU subagent: code + unit tests | code + tests (by subagent, per IU) |
| IU progress checkpoint | updated plan (every 3 IUs) |
| Test subagent: integration/smoke report | report (by subagent) |
| Test analysis + plan revision | updated plan + history |
| Plan revision review | report + updated plan + history |
| Final pass or blocked | updated plan + history |

## Agent Usage

Always spawn fresh agents — context is passed via file paths or inline details, not agent memory.

- **`plan-reviewer`** — launch via `Agent(subagent_type: "think:plan-reviewer")`. Pass plan file path, arch file path, usecase file path, and report output path.
- **`iu-implementer`** — launch via `Agent(subagent_type: "think:iu-implementer")`. Pass IU details (description, file mappings, acceptance criteria, interface contracts). Implements one IU + unit tests. Has chub skill preloaded for API lookups. Independent IUs can be spawned in parallel.
- **`test-runner`** — launch via `Agent(subagent_type: "think:test-runner")`. Pass plan file path. Runs integration and smoke tests, writes the test report. Has chub skill preloaded. Does not classify failures.

## Output Format

Follow the plan template in `${CLAUDE_SKILL_DIR}/references/output-template.md`.
