---
name: domain
description: "This skill should be used when the user needs to extract or revise the cross-cutting Domain Model — concepts, relationships, state transitions — from an existing use-case set. Common triggers include: 'domain model', 'extract concepts', 'glossary', 'class diagram', 'state diagram', 'concept relationships', 'state transitions', 'domain.md', 'reconcile vocabulary'. Writes a4/domain.md (wiki page) following the spec-as-wiki+issues layout. Authored separately from usecase: usecase captures per-UC actor/situation/flow; domain extracts the cross-cutting vocabulary that emerges across UCs."
argument-hint: <optional: "iterate" to resume on open domain review items; otherwise auto-detects existing a4/domain.md>
allowed-tools: Read, Write, Edit, Agent, Bash, Glob, Grep, EnterPlanMode, ExitPlanMode, TaskCreate, TaskUpdate, TaskList
---

# Domain Model Designer

> **Authoring contract:** the contract for `a4/domain.md` lives in `${CLAUDE_PLUGIN_ROOT}/references/domain-authoring.md`. This skill orchestrates the extraction phases.

Takes the use-case set in `a4/usecase/`, the actor roster in `a4/actors.md`, and the problem framing in `a4/context.md`, and extracts the **cross-cutting Domain Model** — the shared vocabulary architecture and implementation will use. Writes the result to `a4/domain.md` as a single wiki page.

This skill exists separately from `/a4:usecase` because cross-cutting concept extraction requires a different reasoning mode from per-UC interview.

## Workspace Layout

Reuse the `a4/` workspace resolved via `git rev-parse --show-toplevel`.

**Inputs:**

- `a4/usecase/*.md` — every Use Case file. Domain concepts surface from cross-UC patterns.
- `a4/actors.md` — actor roster (actors are not domain concepts but inform their relationships).
- `a4/context.md` — problem framing.
- `a4/architecture.md` — *only when iterating after arch has run.* Component names may surface domain-term mismatches.
- `a4/review/*.md` — open items with `target: domain` or `wiki_impact: [domain]` drive iteration.

**Outputs:**

- `a4/domain.md` — single wiki page covering Glossary, Relationships (PlantUML class diagram), State Transitions (PlantUML state diagrams).
- `a4/review/<id>-<slug>.md` — per-finding review items emitted by the wrap-up reviewer.

## Id Allocation

When emitting review items:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/scripts/allocate_id.py" "$(git rev-parse --show-toplevel)/a4"
```

## Modes

- **First Extraction** — `a4/domain.md` does not exist. Run Phase 1 → 2 → 3 in order.
- **Iteration** — `a4/domain.md` exists OR the user said `iterate`. Apply `references/iteration-entry.md` on top of `${CLAUDE_PLUGIN_ROOT}/docs/iterate-mechanics.md`.

`/a4:usecase` does not block on the absence of `domain.md` — it captures actors and per-UC bodies first. Compass routes `UCs exist, domain.md missing → /a4:domain` (Layer 1).

## Session Task List

Phase-level tasks use the phase name. Sub-tasks use `<phase prefix>: <detail>` and are created dynamically when entering a phase.

**First Extraction** — initial tasks:
- `"Step 0: Read sources"` → `in_progress`
- `"Phase 1: Concept Extraction"` → `pending`
- `"Phase 2: Relationship Mapping"` → `pending`
- `"Phase 3: State Transitions"` → `pending`
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

**Iteration** — adjust based on the work backlog:
- `"Review open items and backlog"` → `in_progress`
- One task per selected item / concept
- `"Wrap Up: Reviewer validation"` → `pending`
- `"Wrap Up: Record review items"` → `pending`

## Workflow

### Step 0: Read Sources

Read up front: every file in `a4/usecase/*.md`, `a4/actors.md`, `a4/context.md`, `a4/domain.md` (if exists), `a4/architecture.md` (if exists). Use `Glob` to enumerate UCs, then `Read` each. Mark "Step 0" completed when the read pass is done.

### Phases

In **First Extraction**, run Phases 1 → 3 in order. In **Iteration**, start wherever the user wants. Phase-transition fill-in convention is in `${CLAUDE_PLUGIN_ROOT}/references/domain-authoring.md` §Body shape. Detailed identification heuristics, abstraction guardrails, and diagram conventions are in `references/domain-model-guide.md`.

| Phase | Focus | Procedure |
|-------|-------|-----------|
| 1 | Concept Extraction | `references/phase-concept-extraction.md` |
| 2 | Relationship Mapping | `references/phase-relationships.md` |
| 3 | State Transition Analysis | `references/phase-state-transitions.md` |

### Wrap Up

When the user indicates they're done, run `references/wrap-up.md`: pre-flight consistency check → launch `domain-reviewer` → walk findings → wiki close guard → report.

## File Writing Rules

- **Create `a4/domain.md`** at the end of Phase 1 with the frontmatter and the confirmed `<concepts>` section.
- **Update** at each phase transition using `Edit` where possible. `Write` only for full rewrites.
- **Change-log entries** — append a dated bullet citing the causing UC / spec / review item.
- **`updated:`** — bump on every phase transition or reflected resolution.

## Domain Edits Originating Outside This Skill

`/a4:arch` Phase 3 may edit `a4/domain.md` directly for *simple* changes (concept addition, 1:1 rename, definition wording) without invoking this skill. *Structural* changes (concept split/merge, relationship change, state-transition change) flow through this skill via review items with `target: domain`. The decision table is in `${CLAUDE_PLUGIN_ROOT}/references/domain-authoring.md` §Authorship.

When iterating after arch has run, expect to see `<change-logs>` entries citing `[architecture#<section>](architecture.md#<section>)`. Treat them as authoritative.

## Agent Usage

Context is passed via file paths, not agent memory.

- **`domain-reviewer`** — `Agent(subagent_type: "a4:domain-reviewer")`. Reads `a4/domain.md`, UCs, actors, architecture (if present); writes per-finding review items.

## Non-Goals

- Do not author UCs. UC creation is `/a4:usecase`'s exclusive role.
- Do not edit `architecture.md`. Architectural decisions live there; this skill writes domain only.
- Do not maintain a `domain.history.md`. Per-issue `<log>` sections plus `<change-logs>` and git history cover audit needs.
- Do not track per-source SHAs on `domain.md`.
- Do not emit aggregated reviewer reports. All findings are per-review-item files.
