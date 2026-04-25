# Workflow Mode

a4 workflows operate in one of two modes at any moment. Mode is **session state** — independent of skill boundaries, transitions in-flight as the situation warrants.

## Modes

### `conversational`

- LLM waits for user turn-by-turn input.
- One question at a time; never enqueue multiple decisions in one turn.
- All consequential decisions, approvals, and disambiguations belong to the user.
- Destructive operations (file deletion, force-push, external API writes, schema migrations, etc.) always require explicit user confirmation, even when an autonomous step proposes them.

### `autonomous`

- LLM proceeds from context alone — spawning agents, writing files, transitioning issue status without prompting the user.
- Externally-visible decisions and ratification gates always force a transition to `conversational`.
- A single uninterrupted autonomous run is bounded by the explicit skill scope (e.g., `/a4:run` Phase 2 cycle limit) and by the auto→conv triggers below.

## Session State

Location: `<project-root>/a4/.workflow-state/<session-id>.json`

`session-id` resolution order:
1. `$CLAUDE_SESSION_ID` environment variable when set by the host.
2. SHA256(transcript path) truncated to 16 chars when available.
3. PID-anchored fallback `pid-<pid>-<startup-epoch>` for last-resort uniqueness.

The directory `a4/.workflow-state/` is gitignored.

### File schema

```json
{
  "session_id": "<id>",
  "current_mode": "conversational",
  "entered_at": "<ISO8601>",
  "entered_by": "<skill name or 'session-start'>",
  "trigger": "<short reason>",
  "history": [
    {
      "mode": "conversational",
      "at": "<ISO8601>",
      "by": "<skill name>",
      "trigger": "<reason>"
    }
  ]
}
```

Per-session files prevent races between concurrent Claude Code sessions in the same workspace.

## Lifecycle

| Event | Action |
|-------|--------|
| `SessionStart` (hook) | `workflow_mode.py init` — create the session file with default mode (driven by the first invoked skill's `default_mode`, or `conversational` if mode-less). |
| `SessionStart` (hook, sweep) | `find a4/.workflow-state -mtime +1 -delete` to remove orphan files left by crashed sessions where `SessionEnd` did not fire. Same precedent as `cleanup-edited-a4.sh`. |
| Skill / agent transitions | `workflow_mode.py set <mode> --trigger <reason> --by <skill>` — append to `history`, overwrite top-level fields. |
| `SessionEnd` (hook) | `workflow_mode.py cleanup` — delete this session's file. Always exit 0. |

## Skill Mode Declaration

Each skill's SKILL.md frontmatter declares its mode contract:

```yaml
---
name: <skill>
default_mode: conversational | autonomous
mode_transitions:
  to_conversational: [<trigger keyword or condition>, ...]
  to_autonomous: [<trigger keyword or condition>, ...]
---
```

Mechanical skills (`handoff`, `compass`, `drift`, `validate`, `index`) are mode-agnostic — they may omit both fields. Mode-aware skills must declare `default_mode`.

When a skill is the **first** invocation of a session, the SessionStart hook reads its `default_mode` and seeds the session file. Subsequent skill invocations inherit the live session mode rather than resetting.

## Default Mode by Skill

| Skill | `default_mode` | Notes |
|-------|----------------|-------|
| `idea` | conversational | One-line capture interview. |
| `spark-brainstorm` | conversational | Socratic exploration. |
| `usecase` | conversational | Socratic UC discovery. |
| `auto-usecase` | autonomous | Name reflects mode. |
| `arch` | conversational | Phase-by-phase dialogue; may auto-drill into agents (research, ADR draft) and return. |
| `auto-bootstrap` | autonomous | Name reflects mode. |
| `decision` | conversational | Records a decision reached by conversation. |
| `roadmap` (replaces `plan`) | conversational | Implementation plan authoring. |
| `task` (new) | conversational | Single-task authoring. |
| `run` (new) | autonomous | Agent-driven implement + test loop. |
| `research` | conversational | User-led research sessions. |
| `research-review` | autonomous | Review-agent driven. |
| `handoff`, `compass`, `drift`, `validate`, `index` | n/a | Mechanical infrastructure; mode-agnostic. |

## Transition Triggers (canonical)

### auto → conversational

- An agent's return value carries `clarification_needed: true`, an unresolved decision, or `confidence` below a confidence threshold.
- The current step is a ratification gate (UC ship-review, ADR finalize, destructive operation, external publication).
- A user prompt arrives mid-flight (interpreted as request for control).
- A test-runner or task-implementer surfaces a failure that requires classification (task vs plan vs arch vs UC).
- The autonomous run hits a fixed cycle cap (e.g., `/a4:run` Phase 2 cycle = 3 with failures remaining).

### conversational → autonomous

- The user emits an explicit handoff token. Recognized phrases (Korean / English):
  - `"맡길게"`, `"그대로 진행"`, `"이대로 구현"`, `"실행"`, `"auto"`, `"go ahead"`, `"run it"`, `"proceed"`.
- The user invokes a skill whose `default_mode` is `autonomous` (`/a4:run`, `/a4:auto-bootstrap`, `/a4:auto-usecase`).
- The current step is mechanical (refactor, status flip, batch rename) **and** all decision points are resolved (no open review items targeting the current scope).

Each skill enumerates its own concrete triggers in `mode_transitions` frontmatter. The list above is the workspace-wide canonical set; skills may add specifics, never override these.

## Tool

`scripts/workflow_mode.py` — all callers (hooks, skills, agents) use this single entry point.

```
workflow_mode.py init     [--session <id>] [--mode <mode>] [--by <skill>]
workflow_mode.py get      [--session <id>]
workflow_mode.py set      <mode> --trigger <reason> [--by <skill>] [--session <id>]
workflow_mode.py history  [--session <id>]
workflow_mode.py cleanup  [--session <id>]
workflow_mode.py sweep                                 # called by SessionStart sweep hook
```

`--session <id>` defaults to `$CLAUDE_SESSION_ID`, then to the resolution chain above. Output is JSON on stdout. Exit 0 on success, 1 on usage error, 2 on state-machine violation (e.g., setting a mode that equals the current mode without `--force`).

## Out of Scope (this revision)

- Automatic trigger detection inside skill bodies — skills currently must call `set` explicitly.
- Standardized agent return schema (`clarification_needed`, `confidence`, `decision_pending`) — pending follow-up.
- Conv→auto safety gates (keyword whitelist enforcement, confirmation prompts before destructive auto operations) — pending follow-up.
- Parallel-mode / nested-mode states — modeled as flat for now.

## References

- `references/hook-conventions.md` — hook lifecycle and exit-code conventions, including SessionStart sweep precedent.
- `references/frontmatter-schema.md` — skill frontmatter fields (`default_mode`, `mode_transitions` to be added).
- `spec/2026-04-25-workflow-mode-axis.decide.md` (forthcoming) — design rationale for this axis.
