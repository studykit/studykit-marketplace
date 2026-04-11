# TODO Context

Reference notes from the 2026-04-10 review session. Provides rationale behind decisions and TODO items.

## Checkpoint File Writing (implemented)

### Problem
Interactive skills (think-usecase, think-spec, think-plan, spark-decide) were writing to the output file after every confirmed item. This interrupted conversation flow with frequent Write tool calls.

### Decision
Replaced immediate writes with a **checkpoint approach**:
- Confirmed items are tracked via TaskCreate/TaskUpdate (in-memory, session-scoped)
- File writes happen only at checkpoints: every N items, phase/step transitions, before review, session end
- Tradeoff: small risk of data loss if session is interrupted between checkpoints, but limited to N items max

### Checkpoint intervals
- think-usecase: every 3 UCs
- think-spec: every 3 items per phase
- think-plan: every 3 units
- spark-decide: every 2 options researched

### Not changed
- think-code: orchestrator pattern, Edit for status updates — different concern
- auto-usecase/auto-plan: file-based state machine with commits — different pattern
- spark-brainstorm: already saves at end only
- web-design-mock: version-based output

## Pipeline Handoff (implemented)

### Think pipeline
Added downstream skill suggestions at Finalize (not End Iteration):
- think-usecase → think-spec
- think-spec → think-plan
- think-plan → think-code

### Spark skills
spark-brainstorm and spark-decide are **not pipeline elements**. They are standalone tools.
- spark-brainstorm → spark-decide handoff exists and is appropriate (optional)
- spark-decide had a broken reference to non-existent `co-think-story` — removed entirely
- spark-decide output could optionally feed into think-spec (architecture decisions), but this is not a fixed handoff

### Auto skills
No downstream suggestions added. Waiting for auto-spec to complete the autonomous pipeline. See TODO.md.

## Agent Reuse Guide Removal (implemented)

### Problem
agent-reuse-guide.md instructed skills to offer "reuse existing agent vs spawn fresh" choice on repeated agent invocations.

### Why removed
- All agents receive context via **file paths**, not conversation memory
- Review reports, exploration reports, and history files already capture cross-invocation state
- The "reuse or fresh?" question added unnecessary cognitive burden to users
- think-code and auto-* skills were already using "always fresh" pattern successfully

### Decision
- Deleted `plugins/think/references/agent-reuse-guide.md`
- Updated all SKILL.md files (think-usecase, think-spec, think-plan) and 4 reference files to say "always spawn fresh"
- No behavioral change for spark-decide, web-design-mock (already single-use or stateless pattern)

## File Resolution for think-usecase (implemented)

### Problem
think-spec, think-plan, think-code all had formal File Resolution sections for resolving $ARGUMENTS (full path, partial match, slug). think-usecase lacked this — it treats $ARGUMENTS as an idea, but Iteration Mode needs file resolution.

### Decision
Added resolution logic to Working File Path section:
1. Full path/filename → use directly (Iteration Mode)
2. Partial match → glob `A4/*<argument>*.usecase.md`
3. No existing file → treat as idea, derive slug (New Session)

## Output Path Namespaces (no change)

Intentional design:
- think-*/auto-*: `A4/<slug>.*` — pipeline artifacts
- spark-*: `A4/spark/<date>-<slug>.*` — standalone sessions with date prefix
- web-design-mock: `workflow/web-mock/<slug>/v*/` — HTML/CSS, different artifact type, path set by caller

## auto-plan History File (TODO)

### Why needed
- Consolidates change timeline across quality rounds (currently scattered across review reports and commits)
- Records autonomous decision rationale (strategy choice, unit sizing) in one place
- Enables think-plan to pick up context when iterating on auto-plan output — most practical value

### Current workaround
Review reports + commits + Open Items partially cover this, but require reading multiple files.
