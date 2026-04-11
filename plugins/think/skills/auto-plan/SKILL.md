---
name: auto-plan
description: "This skill should be used when the user wants to autonomously generate a complete implementation plan from a specification without interactive interview. Triggers: 'auto-plan', 'auto-generate plan', 'generate implementation plan', 'create plan from spec automatically', 'no interview just plan', 'run auto-plan on', or when the user provides a .spec.md file and wants a .impl-plan.md file produced without back-and-forth dialogue."
argument-hint: <path to .spec.md file or topic slug>
allowed-tools: Read, Write, Agent, Glob, Grep, Bash, TaskCreate, TaskUpdate, TaskList
---

# Autonomous Implementation Plan Generator

Generate a complete `.impl-plan.md` file from a specification — without human interaction. Make all decisions independently, record assumptions in Open Items, and refine until the plan meets quality standards.

Generate implementation plan for: **$ARGUMENTS**

## Shared References

These files define the rules and format for implementation plan documents. **Do not read them in the main session.** Pass the paths to agents — each subagent reads them per invocation.

- `${CLAUDE_SKILL_DIR}/../think-plan/references/output-template.md` — exact output format
- `${CLAUDE_SKILL_DIR}/../think-plan/references/planning-guide.md` — unit derivation, sizing, dependency, and test strategy guidance
- `${CLAUDE_SKILL_DIR}/../think-plan/references/review-report.md` — how to persist reviewer reports
- `${CLAUDE_SKILL_DIR}/references/session-history.md` — history file format for autonomous decision tracking

If `${CLAUDE_SKILL_DIR}` is not resolved, use `${CLAUDE_PLUGIN_ROOT}/skills/think-plan/references/` instead.

## Resume Detection

Before starting, check for existing progress. If the output file (`A4/<topic-slug>.impl-plan.md`) exists, extract its `reflected_files` list, `last_step`, and `sources` via:

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/read_frontmatter.py A4/<topic-slug>.impl-plan.md reflected_files last_step sources
```

Do not read the output file itself. A file listed in `reflected_files` has already been reflected — do not read it and do not pass it to agents.

1. **Spec change detection:** Compare the stored `sha` in `sources` against the current spec file (`git hash-object <spec-file-path>`).
   - If SHA differs → run `git diff <stored-sha> <current-sha> -- <spec-file-path>` and assess the scope of change:
     - Minor changes (FR additions/modifications, wording) → **resume** from the next step, incorporating the changes.
     - Major changes (strategy change, component restructuring, domain model redesign) → **restart from Step 1**, regenerating the plan entirely.
     - If the spec changes affect file mappings or codebase conventions (e.g., new components, directory restructuring), also check whether the files listed in the plan's file mappings still exist and whether codebase conventions have changed. Factor these findings into the resume/restart decision.
   - If SHA matches → no spec changes, proceed to step 2.
2. **Last completed step:** Extract `last_step` from frontmatter:
   - If set → **resume from the next step** — do not repeat completed work.
   - If empty or absent → no prior progress, start from Step 1.
3. **Review reports:** Check existing `A4/<topic-slug>.impl-plan.review-*.md` files against `reflected_files`. Only pass unreflected review reports to agents.

## Step-by-Step Process

### Step 1: Resolve Input

Resolve the input from **$ARGUMENTS**:

1. **Full path** — use directly if it ends with `.spec.md`
2. **Partial match** — glob for `A4/*<argument>*.spec.md`
3. **Multiple matches** — pick the most recently modified
4. **No match** — report error and stop

Determine the **topic slug** from the spec filename. Output path: `A4/<topic-slug>.impl-plan.md`.

### Step 2: Read Spec and Explore Codebase

Read the spec file thoroughly. Extract:
- All FRs (IDs, types, titles, behavior steps)
- All components (names, responsibilities, schemas, contracts)
- Domain glossary terms
- External dependencies
- Technology stack
- NFRs (if any)

Explore the codebase to understand:
- Directory structure and naming conventions
- Existing file patterns (where services, models, tests live)
- Testing framework and conventions
- Build/package configuration

### Step 3: Derive Implementation Units

Based on the spec analysis, choose an implementation strategy and derive units. Read `${CLAUDE_SKILL_DIR}/../think-plan/references/planning-guide.md` for strategy options.

**Decision rules (autonomous):**
- If spec has 3+ components with DB schemas → **hybrid** (foundation first, then features)
- If spec has independent features with minimal shared state → **feature-first** (vertical slices)
- If spec is primarily a data model with CRUD → **component-first** (bottom-up)
- Default → **hybrid**

For each unit, determine:
- **FRs covered** — map every FR to at least one unit
- **Components involved** — which spec components this unit touches
- **Dependencies** — which other units must be completed first
- **File mapping** — specific file paths based on codebase conventions
- **Test strategy** — type, scenarios, isolation
- **Acceptance criteria** — measurable criteria from FR behavior steps

### Step 4: Build Dependency Graph

Analyze inter-unit dependencies:
1. Check for circular dependencies — if found, restructure units to break cycles.
2. Determine implementation order via topological sort.
3. Identify parallelizable units (no mutual dependencies).
4. Generate the PlantUML dependency diagram and Implementation Order table.

### Step 5: Launch & Verify Detection

Fill the **Launch & Verify** section by auto-detecting values from the spec's Technology Stack and codebase findings from Step 2. Read `${CLAUDE_SKILL_DIR}/../think-plan/references/planning-guide.md` → "Launch & Verify Derivation" for the detection procedure.

For each field:
1. **App type** — detect from dependencies and project structure
2. **Build command** — detect from package scripts, Makefile, or build config
3. **Launch command** — detect from package scripts, launch.json, or framework conventions
4. **Launch URL/view** — derive from app type
5. **Verify tool** — select based on app type (see detection table in planning-guide)
6. **Verify fallback** — select the next-best option for the app type
7. **Smoke scenario** — identify the single most basic user interaction from the spec's FRs

If any value cannot be detected, record it in Open Items as "Launch & Verify: <field> — could not auto-detect, user should specify."

### Step 6: Risk Assessment

Identify cross-cutting risks:
- External service integrations
- Schema migrations on existing data
- Performance-sensitive areas (from NFRs)
- Areas where the spec has Open Items

### Step 7: Write the Plan

Write the complete `.impl-plan.md` file per the output template. Include all sections:
- Overview, Technology Stack, Implementation Strategy
- All implementation units with full details
- Launch & Verify
- Dependency Graph with Implementation Order
- Shared Integration Points (if applicable)
- Risk Assessment
- Open Items (any decisions made autonomously that the user should review)

Update frontmatter:
```yaml
last_step: compose
```

### Step 8: Write History — Compose Entry

Write the initial entry to `A4/<topic-slug>.impl-plan.history.md` per `${CLAUDE_SKILL_DIR}/references/session-history.md`. Record:
- Strategy decision and rationale
- Unit summary (count, FR coverage)
- Key autonomous decisions made during Steps 3–6
- Open Items identified at compose time

If the history file already exists (resume scenario), append the new entry — do not overwrite previous entries.

### Step 9: Verify and Commit

Verify the plan and history files exist at their output paths (do not read them). Commit:
```
impl-plan(<topic-slug>): compose

- Units: <total count>
- FRs covered: <count> / <total>
```

### Step 10: Quality Loop

Repeat until all criteria pass or maximum reached:

1. **Launch a `plan-reviewer` subagent** via `Agent(subagent_type: "plan-reviewer")` with:
   - Plan file path
   - Spec file path
   - Report path per `references/review-report.md` (label: `review-q<round>`)
   - Any previous review report paths

2. If verdict is `ACTIONABLE`:
   a. Append a **Quality Round** entry to the history file — record verdict only (no changes table).
   b. Commit review report + history:
      ```
      impl-plan(<topic-slug>): review <round> — PASS
      
      - Units: <N>
      - All criteria passed
      ```
   c. Exit quality loop.

3. If verdict is `NEEDS_REVISION`:
   a. Read the review report to understand the issues.
   b. Read the current plan file.
   c. Apply fixes directly — update units, dependencies, file mappings, test strategies as needed.
   d. Write the updated plan file. Update frontmatter: `last_step: review-<round>`, add review report to `reflected_files`.
   e. Append a **Quality Round** entry to the history file — record verdict, changes applied, decisions made, and remaining issues.
   f. Commit review report + revised plan + history:
      ```
      impl-plan(<topic-slug>): review <round>
      
      - Units: <total count>
      - Issues fixed: <count>
      - Remaining: <count>
      ```
   g. Continue to next round.

**Maximum:** 3 quality rounds. Remaining issues → Open Items with `[Unresolved after review]`.

### Commit

All commits stage files under `A4/<topic-slug>.*`. Commit timing:
- **After compose** (Steps 7–8) — plan document + history compose entry
- **After each quality round** (Step 10) — review report + history entry (+ revised plan if NEEDS_REVISION)

## Autonomous Decision Rules

Apply these consistently — no human interaction.

1. **Output file exists** → resume per Resume Detection rules.
2. **Strategy choice** → use the decision rules in Step 3.
3. **Ambiguous FR mapping** → assign to the most relevant unit, note in Open Items.
4. **File path uncertainty** → use the codebase patterns found in Step 2. If no pattern exists, use framework defaults.
5. **Never** create GitHub Issues or set `status: final`.

## Final Output

Report to the user:
- Path to generated file
- Number of implementation units
- FR coverage (N / total)
- Component coverage (N / total)
- Implementation strategy chosen and why
- Quality rounds completed
- Review verdict
- Unresolved issues in Open Items
