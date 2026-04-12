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

1. **Full path** — use directly
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
3. **Check unreflected reports** — compare existing report files against `reflected_files`. Read any unreflected reports and reflect them before continuing.
4. Continue from the recorded phase/cycle.

---

## Phase 1 — Plan Generation + Verification

### Step 1: Read Sources

Read the `.arch.md` and `.usecase.md` thoroughly. Extract:
- Technology stack, components, interface contracts
- All FRs (IDs, behavior steps, validation, error handling)
- Domain model, external dependencies
- Test strategy tiers

### Step 2: Explore Codebase

Explore the project to understand structure, conventions, patterns, test setup, and build configuration.

### Step 3: Generate Plan

Enter plan mode. Generate the implementation plan covering:
- Implementation strategy (component-first / feature-first / hybrid) — read `${CLAUDE_SKILL_DIR}/references/planning-guide.md` for guidance
- Implementation units with descriptions, file mappings, dependencies
- Dependency graph and implementation order
- Test plan: unit tests per IU + project-level integration and smoke tests
- Launch & verify configuration

Exit plan mode. Write the plan to `A4/<slug>.plan.md` per `${CLAUDE_SKILL_DIR}/references/output-template.md`.

Record source file SHAs in frontmatter. Set `phase: plan-review`, `revision: 1`.

**Commit:** plan + history

### Step 4: Verification Loop (max 3 rounds)

For each round:

1. Spawn a `plan-reviewer` agent via `Agent(subagent_type: "plan-reviewer")` — pass plan file path, arch file path, usecase file path, and report output path per `${CLAUDE_SKILL_DIR}/references/review-report.md`.

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

### Step 5: Implement + Unit Test

Implement the plan following the implementation order from the dependency graph:

- Write code per IU file mappings and descriptions
- Write unit tests per IU test strategy
- **All unit tests must pass** before proceeding to Step 6

Unit test failures are resolved within this step — they do not consume cycle count.

**Commit:** code + unit tests

### Step 6: Integration + Smoke Test

Run integration and smoke tests as defined in the plan's test plan section.

Write results to `A4/<slug>.test-report.c<N>.md` per `${CLAUDE_SKILL_DIR}/references/test-report.md`.

**Commit:** test report + history entry

### Step 7: Analyze Results

If all tests pass:
- Set `status: complete`
- **Commit:** updated plan + history entry
- Report success to user. Done.

If tests fail — read the report and analyze each failure:
- **Plan issues** → update the plan to address the failures. Add report to `reflected_files`. Increment `revision`. Increment `cycle`. Go to Step 5.
- **Arch/usecase issues** → **stop**. Set `status: blocked`. Report to user with specific issues and which upstream document needs updating.

**Commit:** updated plan + history entry

If cycle 3 exhausted with failures:
- Set `status: blocked`
- **Commit:** updated plan + history entry
- Report to user: current state, all test reports, and remaining failures.

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
pipeline: co-think
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
| Implementation + unit test pass | code + tests |
| Test report written | report + history |
| Test reflection + plan update | updated plan + history |
| Final pass or blocked | updated plan + history |

## Agent Usage

Always spawn fresh agents — context is passed via file paths, not agent memory.

- **`plan-reviewer`** — launch via `Agent(subagent_type: "plan-reviewer")`. Pass plan file path, arch file path, usecase file path, and report output path.

## Output Format

Follow the plan template in `${CLAUDE_SKILL_DIR}/references/output-template.md`.
