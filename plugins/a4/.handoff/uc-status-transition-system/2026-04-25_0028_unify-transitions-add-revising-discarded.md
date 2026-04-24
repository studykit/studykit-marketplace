---
timestamp: 2026-04-25_0028
topic: uc-status-transition-system
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0028. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

This session unified the a4/ status-transition model into a single writer script and introduced two new usecase states (`revising`, `discarded`) plus symmetric enum changes on task and review. It is the first handoff in a new thread (`uc-status-transition-system`); the preceding work on `decision-slot-unification` (split UC `draft` → `draft`+`ready`, introduced `/propagate_superseded.py` + hook for supersedes cascade — final commit `8b67febe4`) provided the groundwork but did not cover the revising/discarded paths, the `dismissed → discarded` review-vocabulary unification, or the move from hook-driven cascade to synchronous single-writer cascade. This session delivered all three.

The user explicitly renamed the session to `uc-status-transition-system` mid-design; treat that as the thread boundary. The `decision-slot-unification` thread is effectively parked (its only remaining open item is writer-less status on `idea.promoted` / `brainstorm.promoted`, which this session did not touch).

Everything below the "Ground rules" section continues to hold from the `decision-slot-unification` → `2026-04-24_2304` handoff. This handoff adds the next layer on top.

All work shipped in a single commit: **`fb93fd986`** (`feat(a4): unify status transitions via transition_status.py`). Plugin version bumped **1.9.0 → 1.10.0**.

# Ground rules locked in this session

These are load-bearing — treat as constraints for future sessions, not suggestions:

- **Single-writer invariant.** Every `status:` change on `usecase/*.md`, `task/*.md`, and `review/*.md` flows through `plugins/a4/scripts/transition_status.py`. Skills and agents invoke it with `--file <path> --to <status> --reason "<text>"`; they never hand-edit `status:` / `updated:` / `## Log` entries. Decision supersedes still uses `propagate_superseded.py` (kept as a PostToolUse hook because `/a4:decision` historically edits the file directly).
- **Hook-free UC cascades.** `shipped → superseded` (via `supersedes:` chain), `implementing → revising` (task reset), and `→ discarded` (task + open-review cascade) are all synchronous inside `transition_status.py`. There is no UC-scoped PostToolUse hook. The rationale: skill/agent call-sites are explicit enough that hook-driven propagation added ambiguity without buying idempotency. The old `propagate-superseded.sh` hook now only gates on `decision/*.md`.
- **`implementing → draft` is permanently disallowed.** Once code has started, the UC cannot roll back to pre-spec-closed. The escape hatches are `implementing → revising` (in-place spec edit, resumes on `revising → ready`) or `implementing → discarded` (abandon). This preserves the "code-involved state only goes forward" principle from the prior thread (which locked `shipped` as forward-terminal).
- **`revising` is transient and in-place.** It is a pause state on the same UC file; no new UC is created for the revision. `revising → ready` re-approves via the existing Step 6 ready-gate in `/a4:usecase`. `revising → discarded` is allowed. `revising → implementing` is **not** — you always go back through the ready-gate so re-approval is explicit.
- **`discarded` is a first-class terminal sink.** It exists on usecase, task, and review. UC `discarded` cascades: tasks that `implements:` this UC → `discarded`; review items with `target: <this-UC>` at `open` / `in-progress` → `discarded`. `complete` tasks are included in the cascade — "the UC is dead, its task history goes dead with it." Code is **not** touched — `discarded` is a spec-layer verdict; separating that from code removal keeps the lifecycle model clean.
- **`dismissed` was renamed to `discarded` on reviews** for cross-family vocabulary unification. There is now one terminal-death word across UC / task / review / idea / brainstorm.
- **Mechanical pre-flight validation lives in the script, semantic in the agent.** The writer enforces: `implemented_by:` non-empty for `ready → implementing`; `actors:` non-empty; `## Flow` section present; no placeholder tokens (`TBD`, `???`, `<placeholder>`, `<todo>`, `TODO:`) in `title:`; every task in `implemented_by:` at `complete` for `implementing → shipped`. The task-implementer agent still judges semantic ambiguity (Flow branches, error-display completeness, actor-mention consistency) but only after the writer's mechanical gates pass.
- **`implemented_by:` is reverse-derived and auto-maintained.** Never hand-write. `scripts/refresh_implemented_by.py` back-scans task `implements:` and populates UC `implemented_by:`. `/a4:plan` Phase 1 calls it after task generation; a session-start sweep catches cross-branch drift.
- **Task cascade depth:** `implementing`/`failing` tasks reset to `pending` on UC `implementing → revising`; `complete` tasks stay. Rationale: the spec is being rewritten, so in-flight work is invalidated, but already-completed-and-committed code does not vanish — `/a4:plan iterate` re-evaluates it against the new spec.

# What got built (commit `fb93fd986`)

## New scripts

### `plugins/a4/scripts/transition_status.py` (~640 lines)

Single-writer for UC / task / review transitions. Structure:

- **Per-family transition tables** (`UC_TRANSITIONS`, `TASK_TRANSITIONS`, `REVIEW_TRANSITIONS`). States absent as keys have no outgoing edges (terminal). Lookup constant-time.
- **Frontmatter IO** (`split_frontmatter`, `rewrite_frontmatter_scalar`, `append_log_entry`, `write_file`) — copied from `propagate_superseded.py` pattern, preserves byte-for-byte formatting outside the edited fields and the `## Log` section.
- **Cascade discovery helpers** — `find_tasks_implementing(uc_ref)`, `find_reviews_targeting(ref)`, `find_usecases_superseded_by(ref)`. Filesystem scan rather than trusting stored reverse-links, so running the script before `refresh_implemented_by.py` still works.
- **Mechanical validation** in `validate_transition(...)` branching on `(from, to, family)`. Currently implements:
  - `ready → implementing` (UC): `implemented_by:` non-empty; `actors:` non-empty; `## Flow` present; `title:` has no placeholder token.
  - `revising → ready` (UC): same shape checks (re-approval).
  - `implementing → shipped` (UC): every task in `find_tasks_implementing(uc_ref)` has `status: complete`.
  - Task and review transitions currently have no mechanical checks.
- **Primary write** (`_apply_status_change`) writes `status:`, bumps `updated:`, appends a `## Log` line `<YYYY-MM-DD> — <from> → <to>[ — <reason>]`.
- **Cascades** (`_cascade_uc_revising`, `_cascade_uc_discarded`, `_cascade_uc_shipped`). Each cascade writes its own Log entries, independent of the primary write. `_cascade_uc_shipped` skips cross-family supersedes entries and is idempotent on already-superseded targets.
- **CLI:**
  ```
  transition_status.py <a4-dir> --file <path> --to <status> [--reason TEXT] [--dry-run] [--force] [--json]
  transition_status.py <a4-dir> --file <path> --to <status> --validate    # no-write verdict
  transition_status.py <a4-dir> --sweep                                    # supersedes recovery
  ```
  `--force` bypasses mechanical validation; illegal transitions are never bypassable. `--validate` returns a `Report` with `validation_issues: [...]` and `errors: [...]`; caller decides what to do.
- **Exit codes:** `0` clean, `2` illegal transition / validation failure / hard error.

### `plugins/a4/scripts/refresh_implemented_by.py` (~200 lines)

Back-scans `task.implements:` and writes `implemented_by:` onto UC frontmatter. CLI:

```
refresh_implemented_by.py <a4-dir>                 # sweep all UCs
refresh_implemented_by.py <a4-dir> --file <path>   # single UC
refresh_implemented_by.py <a4-dir> --dry-run --json
```

Idempotent by design (compares current list to computed; no-op when equal). Writes `implemented_by: [task/10-foo, task/20-bar]` as a flow-style YAML list to stay dataview-friendly. Does **not** touch any field other than `implemented_by:` — it is never a status writer.

Called from:
- `/a4:plan` Phase 1 after task files are generated (see SKILL.md changes below).
- Should also be added to session-start sweeps; the current plan/SKILL.md suggests running it at session-start but this is not enforced by any hook.

## Enum changes

Applied in `scripts/validate_frontmatter.py` (schema enforcement) and `scripts/index_refresh.py` (`TERMINAL_STATUSES` / `IN_PROGRESS_STATUSES`):

- **usecase**: `{draft, ready, implementing, revising, shipped, superseded, discarded, blocked}` (8 values). `TERMINAL_STATUSES['usecase'] = {shipped, superseded, discarded}`. `IN_PROGRESS_STATUSES['usecase']` now includes `revising`.
- **task**: `{pending, implementing, complete, failing, discarded}`. `TERMINAL_STATUSES['task'] = {complete, discarded}`.
- **review**: `{open, in-progress, resolved, discarded}` (was `dismissed`). `TERMINAL_STATUSES['review'] = {resolved, discarded}`.
- **UC `path_list_fields`**: added `implemented_by`.

## Scripts trimmed

- **`propagate_superseded.py`**: usecase entry removed from `TERMINAL_ACTIVE`; docstring rewritten to scope to decision only. Usecase cascade absorbed into `transition_status.py`. `--sweep` mode now only walks `a4/decision/`.
- **`hooks/propagate-superseded.sh`**: path-gate narrowed to `a4/decision/` only. `hooks.json` description updated accordingly. The hook keeps the same timeout (15s) and non-blocking exit-0 behavior.
- **`drift_detector.py`**: `DEDUP_BLOCKING_STATUSES = {"open", "in-progress", "discarded"}` (was `dismissed`). Docstring and a stale user-facing message line updated.

## Validator updates

`scripts/validate_status_consistency.py`:

- Docstring rewritten to describe the new writer split and the `discarded` cascade rules.
- `check_superseded()` messages now name the correct writer (`transition_status.py` for usecase, `propagate_superseded.py` for decision).
- **New `check_discarded_cascade(a4_dir, usecases)`** — flags drift when a UC is `discarded` but its cascades did not run:
  - `missing-discarded-status-task`: task whose every `implements:` entry is `discarded` but task itself is not.
  - `missing-discarded-status-review`: review with `target: <discarded-UC>` at `open` or `in-progress`.
- `collect_workspace_mismatches` now captures the `usecase` dict once and passes it to `check_discarded_cascade`.
- Nothing enforces `revising` cascade consistency (implementing/failing task staying in old state after UC goes `revising`) — could be a follow-up but hasn't surfaced as a need.

## Skill / agent rewrites

### `agents/task-implementer.md`

- Step 1 now calls `transition_status.py --to implementing` with `--json` and surfaces the script's validation issues in `issues:` of the return value rather than duplicating validation in agent prose. `draft` refusal is now expressed as "the script reports an illegal-transition error". No `--force`.
- **New Spec-ambiguity exit section** describes the `implementing → revising` path: allocate an id, write a review item with `kind: finding`, `status: open`, `target: usecase/<X>`, `source: task-implementer`, then call `transition_status.py --to revising --reason "task-implementer: see review/<id>-<slug>"`. Cascade resets related tasks automatically. Return failure with the review item id.
- Rules section tightened: permitted UC interactions are `ready → implementing` and `implementing → revising`; everything else is rejected by the writer.

### `agents/usecase-reviser.md`

- `dismissed → discarded` throughout (section 5 heading + body).
- Section 3 (Close the Review Item) rewritten to call `transition_status.py --to resolved`. Section 5 calls `transition_status.py --to discarded`. Return-summary key renamed `dismissed: → discarded:`.
- Skip condition updated: skip if `status: resolved` or `status: discarded`.

### `skills/usecase/SKILL.md`

- UC frontmatter schema snippet extended: new `revising` / `discarded` values in `status` enum, new `implemented_by: []` field with "auto-maintained" note, rewritten lifecycle explanation (now lists 8 states with descriptions + transition matrix + hard rules).
- Review frontmatter schema updated: `dismissed → discarded`, added `task-implementer` to `source:` options, added trailing note that review status transitions also go through `transition_status.py` and cascade on UC discard.
- Step 6 ready-gate now calls `transition_status.py --to ready` via shell. **Offers both `draft` and `revising` UCs** (was draft-only). Skip conditions updated for the new enum.
- **New "Revising an `implementing` UC" section** documents the user-triggered natural-language flow: confirm the revising flip, call the writer, walk the edit, end on Step 6 ready-gate for `revising → ready`. Mentions preferentially walking `source: task-implementer` review items when present.

### `skills/usecase/references/iteration-entry.md`

- Review item pickup now calls `transition_status.py --to in-progress` instead of hand-editing.
- **New "Revising-UC priority" subsection** describes the scoped-to-one-UC iterate pattern: present task-implementer review items first, flip UC to `revising`, end at `revising → ready`.
- Status summary line now includes `revising`, `shipped`, `discarded`.
- Final iteration-rule on review resolution now points at the writer.

### `skills/usecase/references/session-closing.md`

- Fix-now / Defer / Discard tri-branch for review items now routes resolved and discarded through `transition_status.py`.

### `skills/plan/SKILL.md`

- Task frontmatter schema extended: `discarded` added to status enum with explanation (cascade-flipped by `transition_status.py`).
- Task `status` semantics paragraph notes the revising / discarded cascade rules.
- Step 1.3 (after task generation) now calls `scripts/refresh_implemented_by.py` to populate reverse links. This is **load-bearing**: task-implementer's `ready → implementing` will fail mechanical validation if `implemented_by:` is empty.
- Step 2.1 task-readiness rule now includes "every UC in `implements:` has `status ∈ {ready, implementing}`" — so tasks whose UCs are `revising`/`discarded`/`blocked`/`superseded`/`shipped` are skipped.
- Step 2.2 flips task status via the writer instead of inline edits. Return-value flip also uses the writer.
- Step 2.5 (UC ship-review) calls `transition_status.py --to shipped`; the script enforces "every task complete" and handles the supersedes-chain cascade inline. Removed all reference to the old PostToolUse hook. The "ship-review considers `resolved or dismissed`" clause became "`resolved or discarded`".
- Added a "Session-start resume hygiene revisited" block that routes the `implementing → pending` reset through the writer and recommends `refresh_implemented_by.py` at session start.
- `shipped` terminality clause now explicitly includes `shipped → discarded` as the removal path (alongside supersede-via-new-UC).
- Commit Points mention `transition_status.py` instead of `propagate_superseded.py`.

### Cross-file vocabulary scrub

- `skills/arch/SKILL.md` line 276: "Dismiss" → "Discard" + script call.
- `skills/auto-usecase/SKILL.md`: "resolved / dismissed" in review summary → "resolved / discarded".
- `skills/compass/SKILL.md`, `skills/auto-bootstrap/SKILL.md`, `skills/drift/SKILL.md`: dedup description for drift-detector now cites `discarded` instead of `dismissed`.
- `README.md`: review lifecycle tuple now `open | in-progress | resolved | discarded`.

Not updated (intentional): files under `plugins/a4/spec/*` and `plugins/a4/.handoff/**/*` remain historical snapshots and keep their original `dismissed` terminology. The `decision/SKILL.md` has "quickly dismissed" as prose (not a status), left as-is. `research-review/SKILL.md` has "L dismissed" in verdict summary — it is not a review-item status, left as-is.

## Schema doc (`references/frontmatter-schema.md`)

Rewrites in place (section headings preserved):

- **§Status writers** table rebuilt. Every row now points at `transition_status.py` as the writer (for usecase/task/review) or `propagate_superseded.py` (decision). Added `revising` and `discarded` rows for usecase, `discarded` for task, `discarded` for review. Intro paragraph explicitly names the single-writer invariant.
- **UC table row for `status`** extended to the new 8-value enum. New `implemented_by` row documented with the auto-maintenance caveat.
- **Task `status` enum** extended; **Review `status` enum** renamed `dismissed → discarded`.
- **§UC lifecycle** subsection rewritten: 8-state table + transitions block + notable rules (`implementing → draft` disallowed, `shipped` forward-terminal, `revising` in-place, `ready → implementing` requires `implemented_by:`, `implementing → shipped` requires all tasks `complete`).
- **§Cross-file status consistency** table gained rows for `usecase.implemented_by` (derived by refresh script), `task.status = discarded`, `task.status = pending` (revising cascade), `review.status = discarded`. Each names its active writer.
- **§Cross-references** lists the two new scripts.

# Transition matrix (authoritative)

```
UC:       draft ──► ready | discarded
          ready ──► draft | implementing | discarded
          implementing ──► shipped | revising | discarded | blocked
          revising ──► ready | discarded
          blocked ──► ready | discarded
          shipped ──► superseded | discarded
          superseded ──► (terminal)
          discarded ──► (terminal)

Task:     pending ──► implementing | discarded
          implementing ──► complete | failing | pending | discarded
          complete ──► pending | discarded
          failing ──► pending | implementing | discarded
          discarded ──► (terminal)

Review:   open ──► in-progress | resolved | discarded
          in-progress ──► open | resolved | discarded
          resolved ──► open  (for reopening)
          discarded ──► (terminal)
```

Any edge not listed here is rejected by `transition_status.py` with a clear "allowed from X: [...]" message. The `task.complete → pending` edge exists for `/a4:plan`'s post-failure revision reset; the `task.implementing → pending` edge exists for both session-start hygiene and the revising cascade.

# Verification performed

Fixture directory `/tmp/a4-ts-test/a4/` was constructed with four UCs, two tasks, one review, and two decisions. The following paths were exercised end-to-end:

1. **`draft → ready`** with `--reason` — writes status + Log; confirmed by subsequent file read.
2. **`ready → implementing` with empty `implemented_by:`** — rejected. `validation_issues` lists the empty-list and empty-actors checks; exit 2.
3. **`refresh_implemented_by.py` sweep** — populates `implemented_by: [task/20-do-bar]` on the UC; idempotent second run reports "already up to date."
4. **`ready → implementing` after refresh** — succeeds.
5. **`implementing → revising`** — UC flips; `task/10-do-baz` cascades `implementing → pending` with the correct Log line (`revising cascade: usecase/3-baz`).
6. **Illegal `revising → draft`** — exit 2, `"illegal transition ... allowed from revising: ['discarded', 'ready']"`.
7. **`revising → ready`** — succeeds.
8. **`implementing → shipped` with task `complete`** — succeeds.
9. **Supersedes cascade**: `usecase/4-baz-v2` with `supersedes: [usecase/3-baz]` flipped to `shipped` → old UC-3 cascades `shipped → superseded` in the same invocation; both files modified, both Log lines correct.
10. **`implementing → discarded` with cascade** — task cascades `pending → discarded`, open review cascades `open → discarded`, both with informative Log lines.
11. **Illegal `shipped → draft`** — exit 2.
12. **Illegal `discarded → shipped`** — exit 2, "allowed from discarded: none (terminal)".
13. **Illegal `superseded → shipped`** — exit 2, "allowed from superseded: none (terminal)".
14. **`--validate --to <status> --json`** — returns `Report` with `validation_issues` populated but no write; confirmed by file-mtime check.
15. **`--sweep`** — clean on this fixture ("no supersedes cascades needed").
16. **Trimmed `propagate_superseded.py`** — decision/100-first superseded by decision/101-second via `--file` invocation; worked correctly. Usecase files passed through the script are now silent no-ops (not in `TERMINAL_ACTIVE`).
17. **`validate_frontmatter.py` sweep** — OK, 10 files scanned, no violations (new enums accepted).
18. **`validate_status_consistency.py` sweep** — OK, no mismatches (the discarded cascade ran so no drift).
19. **`index_refresh.py --dry-run`** — rendered successfully with the updated status vocabularies; UC-1 at `ready` surfaces in "implementing: 0" / "ready: appears in static table correctly".

**Not verified:**

- No real a4/ workspace under `plugins/` (prior handoff noted the same — nothing added this session). First production exercise of the revising / discarded / unified-writer flow is pending an actual project.
- `/a4:usecase` natural-language detection of "edit UC X" for an `implementing` UC (the auto-revising flow). Prose is written in SKILL.md but the pattern-match has not been stress-tested.
- Session-start sweep calling `refresh_implemented_by.py` — documented in `/a4:plan` SKILL.md but no hook actually runs it; a session could start with stale `implemented_by:` lists. Consider wiring a SessionStart hook if this becomes painful.
- Cross-thread validator — `validate_status_consistency.py` does not yet verify revising cascade freshness (a UC stuck at `revising` with tasks still `implementing` would be drift).

# Rejected alternatives

Ordered roughly by how much discussion they consumed:

- **`implementing → draft` rollback.** Rejected early and locked in. Rationale: once code is generated, rolling the UC to `draft` creates code/spec divergence with no clean way to reconcile. The alternatives (`revising` in-place, `discarded + new UC`, `implementing → blocked`) cover the realistic scenarios.
- **`implementing → ready` downgrade.** Same-family concern: task state unwind is complex (what happens to committed code? unstaged changes? the implementing agent's progress?). Every path back through `ready` would also re-invalidate the `implemented_by:` list. Keeping `revising` as the single escape from `implementing` avoids this.
- **`revised` (past tense) as a terminal state.** First naming proposal. User countered with `revising` (progressive) because the intent is "this UC is *being* revised in place," not "this UC has been replaced by another file." The progressive-tense naming forced me to make `revising` transient and in-place rather than terminal and new-file-creating. Important distinction — I initially conflated it with `superseded` semantics.
- **New UC + `revises:` forward link** for the revising case. I proposed this at length before the user pointed out that `revising` is on the same file, no new UC needed. The `supersedes:` chain is exclusively for post-ship replacements; mid-implementation edits use `revising`.
- **Separate `dismissed` and `discarded` statuses on reviews.** Discussed as preserving semantic nuance (dismissed = finding invalid; discarded = target dead). Rejected for vocabulary unification. Distinction is preserved by the Log entry reason.
- **Lightweight path (`implementing → ready` pre-flip) for "ambiguity caught before any code written."** Explored as a smoother alternative to `revising` for the early-detection case. Resolved by distinguishing Case A (flip-not-yet-happened — agent refuses at Step 1 pre-flight) from Case B (flip happened, but near-zero code written — still goes through revising). Case A handles the true early-catch cheaply; Case B is the uniform catch-all.
- **Hook-driven UC cascade (status-quo from prior thread).** Considered keeping `propagate-superseded.sh` as the UC cascade writer. User pushed for script-driven ("hook-driven은 필요 없어 보임. script을 이용하여 항상 status 변경하는 구조로"). Benefits realized: synchronous, same-commit, no duplication between hook and validator.
- **Validation level (a) minimal — placeholder + `implemented_by:` only.** Discussed against (b) middle — + actors/Flow and (c) aggressive — LLM semantic scan. User chose (b); script implements `implemented_by:` + `actors:` + `## Flow` presence + placeholder-in-`title`. Flow-actor cross-consistency was deferred as too fuzzy for script; task-implementer agent handles that at coding time.
- **Cross-family `supersedes:` (e.g., decision supersedes usecase).** Already rejected in prior thread; reaffirmed here. Script silently skips such entries with a `cross-family-supersedes` skip reason.
- **Automatic `shipped → discarded` detection by scanning code for UC orphans.** Proposed as option C. Rejected — matching UC Flow to code is heuristic and error-prone. User triggers `shipped → discarded` manually when they remove the feature.
- **Dedicated `/a4:usecase revise <id>` subcommand.** Rejected as friction. The existing `/a4:usecase` session detects the flip from the user's natural-language request ("UC 5 Flow 수정해줘") and confirms before flipping.

# Design principles added (for future sessions)

1. **One writer per family-of-transitions.** `transition_status.py` owns usecase/task/review; `propagate_superseded.py` owns decision. If a new family is added (say `experiment`), either extend `transition_status.py` or split it along a clean axis — do not sprinkle transition logic across skills again.
2. **Script-driven cascade, not hook-driven.** Hooks are appropriate when an external non-script event (user direct edit, tool use) must trigger follow-up. When the trigger is already inside a skill/agent flow, the skill should call the writer directly. Keeps the commit graph clean (one commit, one intent) and removes hook/writer double-validation.
3. **Mechanical vs semantic validation split.** Script checks what can be determined from frontmatter + simple body presence (field shape, required substring). Agent checks what requires understanding (Flow completeness, spec coherence). Don't push semantic checks into the script — they become brittle regex. Don't duplicate mechanical checks in the agent — they become drift sources.
4. **Progressive-tense status names for transient states.** `revising` (not `revised`) because the state ends; `implementing` (not `implemented`) for the same reason. Terminal states use past participles or resultatives (`shipped`, `discarded`, `superseded`, `complete`). This surfaces the lifecycle direction at a glance.
5. **Cascade must be same-commit.** The writer does everything in one invocation so the working-tree delta is one coherent change. If a cascade fails mid-way (e.g., one target file has malformed YAML), it logs to `errors:` but does not try to partially roll back — the caller re-runs with `--force` or fixes the file manually.
6. **Validator mirrors writer.** Every cascade the writer performs has a corresponding drift rule in `validate_status_consistency.py`. If the writer flips X when Y, the validator flags "X is wrong given Y." Keeps the safety-net in sync.

# Plausible follow-ups (not done; user has not requested)

1. **End-to-end in a real workspace.** No real `a4/usecase/`, `a4/task/`, `a4/review/` files exist anywhere in this repo. First production run will exercise: the natural-language "edit UC X" → `revising` detection in `/a4:usecase`; the revising → ready re-approval cadence for multi-edit sessions; the `refresh_implemented_by.py` placement in `/a4:plan` vs. a session-start hook.
2. **SessionStart hook for `refresh_implemented_by.py`.** Currently only called at `/a4:plan` Phase 1 end. If the user runs `git checkout` then starts a session before running `/a4:plan`, `implemented_by:` could be stale and mechanical validation will fail. Low-priority until it bites someone.
3. **Revising-cascade consistency check.** `validate_status_consistency.py` flags discarded-cascade drift but not revising-cascade drift (a UC at `revising` with any `implements:`-linked task still at `implementing` or `failing`). Could be added as `missing-revising-cascade-task`.
4. **`/a4:decision` migration to `transition_status.py`.** The decision family still uses `propagate_superseded.py` + the PostToolUse hook because `/a4:decision` writes `status:` inline. Migrating decision into the unified writer would collapse two mental models into one. Not urgent; the decision path is simpler (no cascades beyond supersedes, no task layer).
5. **`idea.promoted` / `brainstorm.promoted` materialization.** Inherited from the prior thread as still writer-less. Would need a `propagate_promoted.py` or integration into `transition_status.py`. Not touched this session; still parked.
6. **`compass` sweep of the new scripts.** `compass` should probably call `refresh_implemented_by.py --sweep` + `transition_status.py --sweep` + the existing validators. Not wired.
7. **Task enum `spike` / `bug` interaction with `discarded`.** All three task kinds can go to `discarded`. No special handling was added for spike tasks — their sidecar `spike/<id>-<slug>/` directories are not touched by the cascade. Discarded spike tasks leave their sidecars in place, which matches the "discard is spec-layer, not code-layer" rule.
8. **Validator error-message pruning.** `check_superseded` messages now pick the right writer per family, but the discarded-cascade messages always say "transition_status.py should have cascaded" — possible false positive if the discard was legitimately manual (e.g., during migration). Low priority.

# Explicitly untouched

- **Decision family** (except the narrowed `propagate_superseded.py` + hook). `/a4:decision` SKILL.md was not edited; decision still writes `status:` inline. This is the only remaining "hand-edit of status" path under a4/.
- **Idea / brainstorm** — enum unchanged; their `promoted`/`discarded` writers remain as they were in the prior thread (user-driven via consuming skills).
- **`validate_body.py`, `allocate_id.py`, `read_frontmatter.py`, `extract_section.py`, `inject_includes.py`** — not touched.
- **SessionStart / SessionEnd / Stop / PreCompact hooks** — only `propagate-superseded.sh` was modified. The consistency reporters, the edited-a4 recorder, validator, cleanup, and sweep hooks are unchanged.
- **`agents/plan-reviewer.md`, `agents/usecase-reviewer.md`, `agents/usecase-composer.md`, `agents/usecase-explorer.md`, `agents/domain-updater.md`, `agents/api-researcher.md`, `agents/research-reviewer.md`, `agents/mock-html-generator.md`, `agents/test-runner.md`, `agents/arch-reviewer.md`** — not touched.
- **Auto-usecase wrap-up status flip for UCs.** The prior thread's comment ("Do **not** advance any UC past `status: draft` — autonomous generation only produces drafts") still holds; this session did not extend `/a4:auto-usecase` to the writer.
- **Prior-thread handoffs.** `plugins/a4/.handoff/decision-slot-unification/*.md` and all other threads' historical files were not edited (they are snapshots).

# Key files to re-read on the next session

- `plugins/a4/scripts/transition_status.py` — **new**. The canonical writer. Read its module docstring first; then `UC_TRANSITIONS` / `TASK_TRANSITIONS` / `REVIEW_TRANSITIONS` for the full matrix; then `validate_transition` for the mechanical rules; then the three `_cascade_uc_*` functions for the cascade behavior.
- `plugins/a4/scripts/refresh_implemented_by.py` — **new**. Back-link refresher. Docstring covers when to call it.
- `plugins/a4/references/frontmatter-schema.md` — canonical schema. §Status writers and §UC lifecycle sections both rewritten.
- `plugins/a4/agents/task-implementer.md` — Step 1 and the new Spec-ambiguity exit section.
- `plugins/a4/skills/usecase/SKILL.md` — Step 6 ready-gate, new "Revising an `implementing` UC" section.
- `plugins/a4/skills/plan/SKILL.md` — Step 1.3 (refresh_implemented_by), Step 2.1 ready-task rule, Step 2.2, Step 2.5.
- `plugins/a4/scripts/validate_status_consistency.py` — `check_discarded_cascade` is the new safety-net path.
- `plugins/a4/hooks/propagate-superseded.sh` + `plugins/a4/hooks/hooks.json` — decision-scoped hook; description paragraphs updated.

# Outstanding parked threads

- **`uc-status-transition-system`** (this thread) — open. No explicit next step commissioned; candidate next sessions are (a) the `/a4:decision` migration (item 4 above), (b) the SessionStart refresh hook (item 2), or (c) first real-workspace exercise once a project adopts the plugin.
- **`decision-slot-unification`** — effectively concluded. Only remaining open item is `idea.promoted` / `brainstorm.promoted` writer-less materialization, which the prior handoff documented as a design choice rather than a gap. No new findings this session.
- **`a4-redesign`, `experiments-slot`, `idea-slot`** — unaffected.
