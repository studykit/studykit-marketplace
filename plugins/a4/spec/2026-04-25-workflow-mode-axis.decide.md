---
type: decide
pipeline: spark
topic: "Workflow Mode Axis"
date: 2026-04-25
updated: 2026-04-25
status: final
framework: "analysis-driven"
decision: "Introduce a session-scoped workflow mode axis (conversational | autonomous) with per-session JSON state at a4/.workflow-state/<session-id>.json, declared default per skill, transitioned via scripts/workflow_mode.py. Axis is orthogonal to UC-driven vs UC-less project shape and to the skill-boundary axis — modes flow across skills within a single session."
tags: [a4-pipeline, workflow, mode, session-state, hooks]
---
# Decision Record: Workflow Mode Axis

> Source: design conversation triggered while reviewing why the `callgraph-service` workspace (UC-less, ADR-heavy) failed to fit cleanly into the a4 skill set, and why ADR generation never actually fired during `/a4:arch` despite the L213 trigger phrase. The deeper cause was that conversational and autonomous modes were implicit in skill names (`auto-*` for autonomous, others assumed conversational) and mode transitions were skill-boundary-gated — there was no fluid in-session way to drill into autonomous work and return to conversation, or vice versa.

## Context

Skills in this plugin already had two implicit modes:

- **Conversational** — `idea`, `spark-brainstorm`, `usecase`, `arch`, `decision`, `plan` Phase 1, `research`. User drives turn-by-turn.
- **Autonomous** — `auto-usecase`, `auto-bootstrap`, `plan` Phase 2 agent loop, `research-review`. LLM proceeds from context.

But mode existed only as a per-skill static property. Mode transitions were gated by skill switches — to drill from conversational `arch` into autonomous research the user had to invoke `/a4:research`, then come back to `/a4:arch iterate`. Real workflows want fluid transitions:

- During conversational `arch`, an option-defender / decision-drafter agent should run autonomously and return a draft.
- During autonomous `/a4:run` task-implementer, an ambiguity should pause the loop and ask the user.

Without a formal axis, skills could not declare or react to mode in a uniform way, hooks could not act on mode transitions, and tooling could not reason about "what is the session doing right now."

A separate concern: this workspace can host concurrent Claude Code sessions (mobile + desktop, or multiple worktrees). A single-file mode store would race.

## Success Criteria

Ranked:

1. **Mode is first-class state** — declared, observable, transitionable via a single tool. Not a property of skill files alone.
2. **Concurrent sessions are safe** — two Claude Code sessions in the same workspace must not corrupt each other's state.
3. **Orthogonal to other axes** — does not collapse into UC-driven vs UC-less, conversational tone vs LLM autonomy, or skill names. Lives on its own dimension.
4. **Skill authors declare contract, not infrastructure** — adding a new skill means writing `default_mode:` and listing trigger conditions, not implementing state management.
5. **Hook integration is mechanical** — SessionStart / SessionEnd lifecycle is the same shape as existing `cleanup-edited-a4` precedent.

## Decision

### Two named modes, session-scoped state, single tool

**Modes**:

- `conversational` — LLM waits for user turn-by-turn input. One question per turn. Destructive operations always require explicit user confirmation even when an autonomous step proposes them.
- `autonomous` — LLM proceeds from context: spawns agents, writes files, transitions issue status without user prompt. Externally-visible decisions and ratification gates always force a transition back to `conversational`.

**State location**: `<project-root>/a4/.workflow-state/<session-id>.json`. Per-session file prevents races.

**`session-id` resolution order**:
1. Explicit `--session` argument
2. `$CLAUDE_SESSION_ID` environment variable
3. `SHA256($CLAUDE_TRANSCRIPT_PATH)` truncated to 16 hex chars
4. `pid-<pid>-<startup-epoch>` last-resort fallback

**File schema** (full spec lives at `plugins/a4/references/workflow-mode.md`):

```json
{
  "session_id": "...",
  "current_mode": "conversational | autonomous",
  "entered_at": "<ISO8601>",
  "entered_by": "<skill name>",
  "trigger": "<short reason>",
  "history": [{"mode": "...", "at": "...", "by": "...", "trigger": "..."}]
}
```

**Tool**: `plugins/a4/scripts/workflow_mode.py` — single entry point. Subcommands `init`, `get`, `set <mode> --trigger <reason>`, `history`, `cleanup`, `sweep`. Atomic writes via `.tmp` rename. JSON output. Hooks and skills both call this.

### Lifecycle (hook-driven)

| Event | Action |
|-------|--------|
| `SessionStart` | `workflow_mode.py init` (create with first skill's `default_mode`, fall back to `conversational`) |
| `SessionStart` (sweep) | `find a4/.workflow-state -mtime +1 -delete` for orphaned session files; mirrors `sweep-old-edited-a4.sh` |
| Skill / agent transitions | `workflow_mode.py set <mode> --trigger <reason> --by <skill>` |
| `SessionEnd` | `workflow_mode.py cleanup` deletes this session's file |

### Skill mode declaration

Each mode-aware skill declares in SKILL.md frontmatter:

```yaml
---
default_mode: conversational | autonomous
mode_transitions:
  to_conversational: [<trigger keywords or conditions>]
  to_autonomous: [<trigger keywords or conditions>]
---
```

Mechanical skills (`handoff`, `compass`, `drift`, `validate`, `index`) are mode-agnostic and may omit both fields.

### Default mode by skill

| Skill | `default_mode` |
|-------|----------------|
| `idea`, `spark-brainstorm`, `usecase`, `arch`, `decision`, `roadmap`, `task`, `research` | conversational |
| `auto-usecase`, `auto-bootstrap`, `run`, `research-review` | autonomous |
| `handoff`, `compass`, `drift`, `validate`, `index` | n/a (mode-agnostic) |

### Canonical transition triggers

**auto → conversational**:
- Agent return value carries `clarification_needed: true`, unresolved decision, or `confidence` below threshold
- Ratification gate: UC ship-review, ADR finalize, destructive operation, external publication
- User prompt arrives mid-flight (interpreted as request for control)
- task-implementer / test-runner failure requiring classification (task / roadmap / arch / UC)
- Autonomous run hits a fixed cycle cap (e.g., `/a4:run` Phase 2 cycle = 3 with failures remaining)

**conversational → autonomous**:
- Explicit handoff token: `"맡길게"`, `"그대로 진행"`, `"이대로 구현"`, `"실행"`, `"auto"`, `"go ahead"`, `"run it"`, `"proceed"`
- User invokes a skill whose `default_mode` is `autonomous` (`/a4:run`, `/a4:auto-bootstrap`, `/a4:auto-usecase`)
- Step is mechanical (refactor, status flip, batch rename) **and** all decision points are resolved (no open review items targeting the current scope)

Skills enumerate their own concrete triggers in `mode_transitions` frontmatter. The above is the workspace-wide canonical set; skills may add specifics, never override.

### What the axis is **not**

- Not a property of skills only — modes flow across skill boundaries within a single session.
- Not a synonym for UC-driven vs UC-less — UC-less projects can run in either mode (a callgraph-service-style ADR-heavy session may run conversationally during arch and autonomously during `/a4:run`).
- Not a per-agent attribute — agents return values that may trigger mode changes; agents do not own mode themselves.
- Not gitignored as a directory I should pretend doesn't exist — it is openly part of the workspace, just session-scoped.

## Out of Scope (this revision)

Pending follow-ups, not part of this ADR's commitment:

- **Auto-detect transitions from conversation content** — skills currently must call `workflow_mode.py set` explicitly. A future revision can add UserPromptSubmit hook detection for the canonical conv→auto keywords.
- **Standardized agent return schema** (`clarification_needed`, `confidence`, `decision_pending`) — agents currently return ad-hoc fields. Consolidation will come with the agent-return-schema revision.
- **Conv→auto safety gates** — keyword whitelist enforcement, confirmation prompts before destructive auto operations are not yet implemented.
- **Parallel / nested mode states** — modeled as flat. A nested-stack model can be added if a real use case demands it.

## Rejected Alternatives

| Option | Reason |
|--------|--------|
| **Single workspace-level state file** (`a4/.workflow-state.json`) | Concurrent sessions race. The user has confirmed mobile+desktop+worktree concurrency as a real scenario, not a theoretical one. |
| **Mode as a per-skill static property only** (no session state) | Cannot represent "we are currently in mode X" across skill invocations. Skill chains lose mode coherence. |
| **Embed mode in transcript-derived state without a script** | Hooks would need to parse the transcript on every event. Tool-mediated state is faster, observable, and inspectable by users. |
| **Use `mode: planning | implementing | shipping`** (workflow stage instead of mode) | Conflates stage with mode of operation. A planning stage can be either conversational or autonomous; shipping can also straddle both. |
| **Make mode a folded property of `compass`** (compass tells you "what mode are you in") | compass is a navigator, not state. The compass output should reflect mode, not own it. |
| **Don't introduce mode formally; rely on existing `auto-*` naming convention** | Naming convention only marks the *default* mode of a skill. It cannot track in-session transitions, support fluid drilling, or be observed by hooks. |
| **`mode: interactive | unattended`** (alternative naming) | Considered but `conversational | autonomous` better reflects the actual behavior — a conversational mode is not just "interactive" (mechanical mode is also interactive in that the user can stop it at any moment), and `autonomous` more accurately conveys what the LLM does in that mode than `unattended`. |

## Migration

- The spec document `plugins/a4/references/workflow-mode.md` carries the full operational reference — read that before authoring or modifying mode-aware skills.
- The script `plugins/a4/scripts/workflow_mode.py` is the single tool entry point; do not write a parallel implementation.
- `a4/.workflow-state/` is gitignored at the consuming-workspace level (each project that uses a4 must add this entry; the plugin does not edit user `.gitignore` automatically — readme guidance handles this).

## Discussion Log

<details>
<summary>Conversation summary</summary>

**Trigger.** Mid-discussion of `callgraph-service` (UC-less, 44 ADRs) the user observed: "먼저 사람과 대화하는 workflow인지 완전 LLM 자동형인지를 구분할 필요가 있어 보임. LLM으로 자동으로 돌리다가 중간에 대화형 workflow로 진입할 수 있어야함. 대화형 workflow로 진행하다, 중요사항이 결정된 뒤에는 LLM이 자동으로 구현할 수 있어야함."

**Reframe.** Earlier discussion had centered on UC-driven vs UC-less project shapes (callgraph-service was UC-less). The mode axis is orthogonal: both project shapes can run in either mode, and modes transition mid-session.

**Concurrent sessions.** The user flagged that single-file state would race across simultaneous Claude Code sessions in the same workspace. Decision: per-session JSON files keyed by `session-id` with the resolution chain above.

**plan rename context.** This ADR landed in the same session as the `/a4:plan` → `/a4:roadmap` rename. The two are recorded as separate ADRs because they have independent rationale (this one is about modes; the rename is about the planning/orchestration role separation).

**Backwards-compatibility.** User direction: do not consider backwards-compat. Validators reject any `kind: plan` immediately; the rename is forward-only.

</details>
