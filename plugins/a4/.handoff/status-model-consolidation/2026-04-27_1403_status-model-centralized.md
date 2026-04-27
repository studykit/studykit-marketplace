---
timestamp: 2026-04-27_1403
topic: status-model-consolidation
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-27_1403. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Session focus

Two threads, executed in order:

1. **Lifecycle question — should `open` replace `pending` in task status?**
   Outcome: **rejected**. Both states stay; rationale captured below.
2. **Consolidation refactor — status data was duplicated across four scripts.**
   Outcome: **shipped** as `refactor(a4): centralize status model in status_model.py` (commit `b4d88012a`).

## Thread 1 — `open` vs `pending` (decision: keep both)

### Trigger

Just-merged commit `204091f4a` added `open` (kanban backlog) alongside the existing `pending` (work queue). User questioned whether the two could be collapsed by having `open` replace `pending`.

### Conclusion

Replacement is **not advisable**. The two states encode different bits:

| State | Commit-to-queue? | `/a4:run` picks up? |
|-------|------------------|---------------------|
| `open` | no (backlog capture) | ✗ |
| `pending` | yes (enqueued) | ✓ |

Folding `pending` into `open` breaks four things:

1. **Loss of `/a4:run` safety guardrail.** `/a4:task` is a capture verb. If every captured task auto-runs, you can no longer "just record this idea."
2. **Cascade target semantics break.** UC `revising` cascade resets `progress`/`failing` → `pending`; `failing → pending` defer; `complete → pending` re-impl. All target `pending` because they mean *"already-committed-to-queue, re-enqueue"*. Routing them to `open` demotes them to backlog and erases the distinction.
3. **`/a4:roadmap` fill-queue intent disappears.** Roadmap emits `pending` to mean "fill the queue right now." Same state as `/a4:task`'s capture would lose that distinction.
4. **Direct contradiction with the just-merged design.** Schema explicitly states `open` is *"Not picked up by `/a4:run`."* A replacement would force redefinition.

### Note for future revisits

The reverse direction (delete `open`, keep `pending`) is more coherent if simplification ever becomes necessary — fewer collisions, but loses the kanban-style backlog guardrail that was just added. Reasonable trigger to revisit: empirical evidence that `open` is rarely used (e.g., 90%+ of tasks bypass it and create directly at `pending`). Until that signal appears, keep both.

## Thread 2 — status_model.py centralization (shipped: `b4d88012a`)

### Motivation

`204091f4a` touched 17 files for one rename + one new value. Survey showed status enums and transition tables duplicated across four scripts:

- `transition_status.py` — `FAMILY_STATES`, `FAMILY_TRANSITIONS`, four per-family `*_TRANSITIONS`
- `validate_frontmatter.py` — literal `frozenset({...})` in each `Schema.enums["status"]`
- `workspace_state.py` — `TERMINAL_STATUSES`, `IN_PROGRESS_STATUSES`, `BLOCKED_STATUSES`, `ACTIVE_TASK_STATUSES`
- `search.py` — `STATUS_BY_FOLDER`, `KIND_BY_FOLDER`

User accepted plan A (import consolidation). Implementation:

### Files in `b4d88012a`

- **NEW** `plugins/a4/scripts/status_model.py` — canonical module exporting `STATUS_BY_FOLDER`, `FAMILY_TRANSITIONS` (with hierarchical `UC_TRANSITIONS` / `TASK_TRANSITIONS` / `REVIEW_TRANSITIONS` / `DECISION_TRANSITIONS`), `TERMINAL_STATUSES`, `IN_PROGRESS_STATUSES`, `BLOCKED_STATUSES`, `ACTIVE_TASK_STATUSES`, `KIND_BY_FOLDER`. All values are `frozenset`.
- `plugins/a4/scripts/transition_status.py` — dropped inline tables; imports from `status_model`. Internal alias `STATUS_BY_FOLDER as FAMILY_STATES` keeps existing call sites untouched. Note: `STATUS_BY_FOLDER` includes `idea` and `spark` keys, but `FAMILY_TRANSITIONS` does not (idea/spark have no mechanical writer); `detect_family` only returns keys present in `FAMILY_TRANSITIONS`, so the extra keys never hit the writer.
- `plugins/a4/scripts/validate_frontmatter.py` — `SCHEMAS` enums now reference `STATUS_BY_FOLDER["..."]` and `KIND_BY_FOLDER["..."]`. `spark_brainstorm` schema looks up `STATUS_BY_FOLDER["spark"]` (folder name, not schema name).
- `plugins/a4/scripts/workspace_state.py` — imports the four classification sets. `SPARK_TERMINAL` rebuilt as `{"brainstorm": TERMINAL_STATUSES["spark"]}` (file-flavor key vs folder key).
- `plugins/a4/scripts/search.py` — `STATUS_BY_FOLDER` imported directly. `KIND_BY_FOLDER` is a local dict that spreads the model's `KIND_BY_FOLDER` and adds `"wiki": frozenset(WIKI_KINDS_TUPLE)` (wiki kinds are local to search.py because it owns the ordered tuple). Imports the model version with alias `_MODEL_KIND_BY_FOLDER` to avoid name shadowing.
- `plugins/a4/references/frontmatter-schema.md` — Cross-references section gained a "Status model (canonical): scripts/status_model.py" entry above the writer entry.
- `plugins/a4/CLAUDE.md` — added one-liner under "Skill-generated frontmatter is script-managed": *"Status enums, transitions, and terminal/in-progress sets live in `scripts/status_model.py` — the canonical model imported by the writer, validators, workspace state, and search. Add new status values there first; consumers pick them up automatically."*

### Verification done

- All four consumer scripts: `python -c "import ..."` succeeds; key constants match expectations; `--help` renders.
- End-to-end fixture: tmp `a4/` with `architecture.md`, `usecase/1-foo.md`, `task/2-bar.md`, `spark/2026-04-27-1000-baz.brainstorm.md`. Ran:
  - `validate_frontmatter` → `OK — 4 file(s) scanned, no violations.`
  - `search --status open` → returns task and spark items correctly
  - `workspace_state` → dashboard renders with correct stage progress

### Not in scope (deferred)

The original plan A had three bullets. Bullets 1+2 (consolidation) shipped. Bullet 3 was deferred:

> **Transition diagram generator + drift detection.** A small script that emits the transition ASCII blocks of `references/frontmatter-schema.md` from `status_model.py`, with a `--check` mode for hooks to flag doc/code drift.

This is a clean, separate chunk. Worth revisiting if/when the schema doc's hand-written diagrams drift from the code (which now requires updating both `frontmatter-schema.md` prose and `status_model.py`, but the doc is no longer the canonical model).

### Other duplication that did NOT need consolidation

Audited remaining scripts for status-enum duplication:

- `validate_status_consistency.py` — uses literal status names in cross-file consistency rules (e.g., `"decision": "final"`, `"usecase": "shipped"` for "successor must hit this status to trigger superseded"). These are flow-specific, not enum tables. Leave as-is.
- `drift_detector.py` — has narrow local set `DEDUP_BLOCKING_STATUSES = {"open", "in-progress", "discarded"}` for review-item dedup logic. Local-scope, leave as-is.
- `refresh_implemented_by.py`, `register_research_citation.py`, `a4_hook.py`, `validate.py` — no status enum tables, just flow-specific literal references where they are appropriate.

### Skill prose status references (out of scope here)

`grep -rln "status.*pending\|status.*open\|status.*progress" plugins/a4/skills/ plugins/a4/agents/` found 20+ SKILL.md / agent files that mention status values in prose. These were NOT touched in this refactor. Updating them is a separate chunk (the original plan's "C — skill prose consolidation"); the user did not ask for it. Recommendation if revisited: replace inline status descriptions with one-line links into `references/frontmatter-schema.md` so prose lives in one place. Trade-off is loss of inline LLM context vs. progressive disclosure cost.

## Repo state at handoff

- Branch: `main`, ahead of `origin/main` by 2 commits (the prior `204091f4a` task-lifecycle commit and today's `b4d88012a` refactor).
- Working tree: clean.
- No outstanding TODOs from this session.

## Pointers for the next session

- **Adding a new status value.** Edit `plugins/a4/scripts/status_model.py` first. If it needs mechanical transitions, also edit the corresponding `*_TRANSITIONS` dict in the same file. Update the prose tables in `plugins/a4/references/frontmatter-schema.md` to match (still hand-maintained — see deferred bullet 3 above).
- **Adding a new family.** Add a new key to `STATUS_BY_FOLDER`, classification dicts, and (if mechanical) `FAMILY_TRANSITIONS`. Add a `Schema` entry in `validate_frontmatter.py`. The model is folder-keyed; the validator's `spark_brainstorm` schema is the only place where schema-name and folder-name diverge (uses `STATUS_BY_FOLDER["spark"]`).
- **`open` vs `pending` debate.** Don't relitigate without empirical signal. See Thread 1 above.
- **Topic-thread continuation.** This `status-model-consolidation` topic is open. Future status-model work (the deferred diagram generator, kind-enum unification beyond what's done, etc.) should chain handoffs under the same `topic:` and the `<topic>/` subdirectory.
