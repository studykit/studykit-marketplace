---
timestamp: 2026-04-24_2304
topic: decision-slot-unification
previous: 2026-04-24_2231_assign-writers-to-remaining-statuses.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_2304. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Direct continuation of `decision-slot-unification`. The preceding handoff (`2026-04-24_2231`) had just closed the four unacceptable gaps where status enum values had no writer, but left two structural concerns untouched:

1. The UC lifecycle still collapsed "being written" and "spec closed, waiting to be implemented" into a single `draft`. `task-implementer` would pick up any `draft` UC, which created a real risk of coding against an unfinalized spec.
2. `decision.superseded` still had no writer — it was surfaced only by the consistency validator. The user opened this session by saying "파일에 기록을 안하면 찾기가 힘든 점이 있음" — that purely-derived statuses are effectively invisible when you read a single file.

Layered on top: the user explicitly rejected going `shipped → implementing` ("usecase status를 done으로 수정한후 implementing으로 가는건 직관적이지 않음"), which made `done` semantically wrong — `done` felt reversible, while what the user meant was "the system actually reflects this", which is a fact statement.

The session converged on three design choices and then executed them:

- **Split UC `draft` into `draft` + `ready`**, rename `done` → `shipped`, add `superseded`. New enum: `draft | ready | implementing | shipped | superseded | blocked`.
- **Revision after ship = new UC with `supersedes: [<old>]`**, not `shipped → draft` rollback. `shipped` is strictly terminal on the forward path. This was the user's proposal ("revise가 필요한 경우는 usecase를 새로 만들는게 history관리가 편해 보이는데") — history stays append-only.
- **Materialize `superseded` via a script-triggered PostToolUse hook**, covering both `usecase` and `decision` families symmetrically. "파생 status라도 writer를 둘 수 있으면 파일에 기록한다" — the validator becomes a safety net, not the primary surface.

All work shipped in a single commit: **`8b67febe4`** (feat(a4): split UC lifecycle into draft/ready/impl/shipped/superseded). Version bumped **1.8.0 → 1.9.0**.

# Ground rules locked in this session

These are load-bearing for future sessions — treat them as constraints, not suggestions:

- **UC `shipped` is terminal on the forward path.** There is no `shipped → implementing` and no `shipped → draft`. Revision is modeled only by creating a new UC that declares `supersedes: [usecase/<old-id>-<slug>]`.
- **`task-implementer` refuses `draft`.** The only accepted input status is `ready`. A `draft` UC in the task's `implements:` list is a hard failure; the agent returns without touching any file and names the blocking UC.
- **`ready` is user-confirmed, not automatic.** `/a4:usecase` wraps up with a per-UC ask ("mark as ready to implement?") — silence keeps the UC at `draft`. Auto-generation skills (`/a4:auto-usecase`, `usecase-composer`) must never advance past `draft`.
- **Materialize derived statuses whenever a writer exists.** `superseded` is derived from `supersedes:` relationships — but both families now get actively written. `validate_status_consistency.py` stays the drift surface for the two writer-less `promoted` cases (`idea`, `brainstorm`) and as a safety net for `superseded` when the hook couldn't run (bulk sweeps, bypass).
- **`supersedes:` is always same-family.** A usecase cannot supersede a decision and vice versa. The propagation script skips cross-family refs as `skipped: cross-family-ref`.

# What got built (commit `8b67febe4`)

## Enum + schema changes

- `plugins/a4/scripts/validate_frontmatter.py` — usecase `status` enum extended to `{draft, ready, implementing, shipped, superseded, blocked}`. `supersedes` added to usecase's `path_list_fields`.
- `plugins/a4/scripts/index_refresh.py` — `TERMINAL_STATUSES['usecase']` becomes `{shipped, superseded}` (was `{done}`); `TERMINAL_STATUSES['decision']` gains `superseded` alongside `final`.
- `plugins/a4/references/frontmatter-schema.md`:
  - UC row updated to the new enum.
  - `supersedes` row in structural-relationship table extended to apply to both `decision` and `usecase`.
  - New **UC lifecycle** subsection explaining each of the five forward states + `blocked`, with the "`shipped` is terminal" rule.
  - **Status writers** table rewritten: `usecase.superseded` and `decision.superseded` now point at `propagate_superseded.py` instead of being "derived — no writer".
  - **Cross-file status consistency** table updated to 4 rows (adds `usecase.status = superseded`), and a new "Materialized by" column distinguishes actively-written rules from report-only ones.
  - Closing paragraph reframes the principle: materialize when a writer is possible; validator is the fallback.

## `/a4:usecase` — ready-gate at wrap-up

`plugins/a4/skills/usecase/SKILL.md` Wrapping Up now has a **Step 6 (Ready-gate)** inserted before the summary. It only offers UCs currently at `draft`; `ready`/`implementing`/`shipped`/`superseded`/`blocked` are skipped. Per-UC natural-language acceptance ("yes"/"ok"/"확정"/"mark ready") flips `draft → ready`, bumps `updated:`, and appends a `## Log` entry with today's date. Silence or "아직" keeps `draft`. Summary (now Step 7) reports UC counts including the `ready` flip count.

The UC schema snippet at the top of the skill also got expanded: added `supersedes: []` line, added a lifecycle paragraph describing all five forward states, and the terminality of `shipped`.

## `task-implementer` — accept only `ready`

`plugins/a4/agents/task-implementer.md` Step 1 now branches explicitly on status:
- `ready` → flip to `implementing`, bump `updated:`.
- `implementing` / `shipped` / `superseded` / `blocked` → leave alone.
- `draft` → **refuse**. Return failure, name the blocking UC, do not touch any file. Instruct user to run `/a4:usecase` to hit the ready-gate.

The Rules section was also tightened: the permitted UC edit is now `ready → implementing` (was `draft → implementing`). A `draft` UC is explicitly not implementable.

## `/a4:plan` Step 2.5 — rename to ship-review

`plugins/a4/skills/plan/SKILL.md` Step 2.5 heading becomes **UC ship-review (user-confirmed)**. Every mention of `done` replaced with `shipped`. Key behavioral additions:

- Step 4 now notes: "If the newly-shipped UC has a non-empty `supersedes:` list, **do not** hand-edit the targets here — the hook will flip each target from `shipped` to `superseded` automatically." The plan skill is not responsible for propagation.
- Step 5 clarifies that hook-driven `superseded` flips on predecessor UCs land in the same working-tree change as the ship edit, so they belong in the same commit naturally.
- New terminal paragraph: "**`shipped` is terminal.** If a UC needs revision later, the right move is to create a new UC via `/a4:usecase` with `supersedes: [usecase/<old>]`..."
- Commit Points entry for Step 2.5 renamed to "UC ship-transitions" with message prefix `docs(a4): ship UC <ids>` (was `docs(a4): mark UC <ids> done`).

## `propagate_superseded.py` — the new active writer

`plugins/a4/scripts/propagate_superseded.py` (new, ~280 lines). Core contract:

Given a file path to `a4/usecase/*.md` or `a4/decision/*.md`, check:
- `(a)` the file is at its family's terminal-active status (`usecase=shipped`, `decision=final`),
- `(b)` its `supersedes:` list is non-empty.

If both hold, for each same-family target in `supersedes:`:
1. Flip target `status → superseded` (only if target is currently at the family's terminal-active; already-`superseded` is a silent skip).
2. Bump `updated:` to today.
3. Append `- YYYY-MM-DD — superseded by <family>/<stem>` under `## Log` (creates the section if absent).

**Important design details:**

- **Script does its own frontmatter rewriting.** Does not use yaml.dump — preserves surrounding frontmatter formatting and body content byte-for-byte outside the edited fields. See `_rewrite_frontmatter_scalar` for the line-by-line rewrite logic.
- **Idempotent.** Re-running on the same successor is a no-op; already-superseded targets report as `skipped: already-superseded`.
- **Cross-family refs are skipped, not errored.** A usecase with `supersedes: [decision/X]` is malformed but the script logs it as `skipped: cross-family-ref` and moves on.
- **Exit codes.** `0` on clean run including no-op runs; `2` only on hard errors (malformed YAML in successor, missing a4 dir). Lets the hook treat no-op and success identically.
- **`--sweep` mode** walks every file in `a4/usecase/` and `a4/decision/` — useful for recovery after mass edits where the hook didn't fire (e.g., git checkout, bulk rebase). Idempotent by design.
- **`--dry-run`** prints planned changes without writing; combined with `--json` gives a machine-readable change manifest.

CLI shape:

```
uv run propagate_superseded.py <a4-dir> --file <path>          # standard hook invocation
uv run propagate_superseded.py <a4-dir> --file <path> --dry-run --json
uv run propagate_superseded.py <a4-dir> --sweep                # recovery
```

## `propagate-superseded.sh` — the PostToolUse hook

`plugins/a4/hooks/propagate-superseded.sh` (new, executable). Shape mirrors the existing `report-status-consistency-post-edit.sh`:

- Gates on `Write|Edit|MultiEdit` tool_name.
- Gates on file path matching `$CLAUDE_PROJECT_DIR/a4/usecase/*` or `$CLAUDE_PROJECT_DIR/a4/decision/*`.
- Runs the script in `--json` mode, parses `total_propagated` and `total_errors`.
- If zero changes and zero errors → silent exit 0.
- If changes happened → emits `additionalContext` with a bulleted list of targets flipped + a reminder that the flipped-target edits are unstaged and should land in the same commit.
- Always exits 0 (non-blocking by design, consistent with the existing consistency hook).

Registered in `plugins/a4/hooks/hooks.json` as the second entry in the `PostToolUse[Write|Edit|MultiEdit].hooks` array, between `record-edited-a4.sh` and `report-status-consistency-post-edit.sh`. Timeout: 15 seconds. `hooks.json` description updated to mention both consistency reporting (informational) and supersedes propagation (actively writes).

## Validator update

`plugins/a4/scripts/validate_status_consistency.py` generalized:

- New constant `SUPERSEDES_FAMILIES = {"decision": "final", "usecase": "shipped"}`.
- `check_superseded()` now takes `(items, family)` — same logic for both families, only the expected terminal-active status differs.
- **Crucial behavior change**: the rule now scopes to "successor at terminal-active". A `draft` UC with `supersedes: [X]` does NOT flag X as missing-superseded, because the replacement hasn't actually landed yet. This matches the script's trigger condition — validator and writer agree on when a target "should be" superseded.
- `collect_decisions()` kept as a back-compat alias over new `collect_family()`. `_decision_component()` kept as alias over new `_supersedes_component()`.
- File-scoped mode now walks UC supersedes chains too — editing a UC in a supersedes chain surfaces only the connected component, same pattern as decisions.
- Rule names gain `-usecase` / `-decision` suffixes: `stale-superseded-status-decision`, `missing-superseded-status-usecase`, etc.
- Module docstring rewritten to describe the four derived rules (adds UC.superseded) and the division of labor: hook actively writes; validator is the safety net for "hook didn't run / was bypassed / bulk sweep left drift".

## Docs pointing at each other

- Schema doc `§Status writers` table links inline to `scripts/propagate_superseded.py` and frames the writer/safety-net split.
- Schema doc `§Cross-file status consistency` table gains a "Materialized by" column so a reader can see at a glance which rules have a writer vs. which are drift-report-only.

# Verification performed

Fixture-based tests of `propagate_superseded.py` at `/tmp/propagate_test/`:

1. **Dry-run sweep** on mixed UC + decision workspace — reported 2 planned changes, wrote nothing.
2. **Real invocation** on both families — target files correctly flipped, `updated:` bumped, `## Log` entry appended; Log section created where absent.
3. **Idempotency** — re-running the same `--file` produced `propagated: 0, skipped: [{reason: already-superseded}]`.
4. **Successor at `draft`** — `supersedes:` populated but `status: draft` → no-op, target untouched.
5. **Cross-family ref** — usecase with `supersedes: [decision/X]` → `skipped: cross-family-ref`, target untouched.

Fixture-based tests of `validate_status_consistency.py`:

6. Generalized validator correctly flags UC `missing-superseded-status-usecase` when a `shipped` successor exists, and flags stale decision `superseded` when no live successor claims it. Confirms the "successor must be at terminal-active" scoping — a `draft` successor does NOT trigger the flag.
7. File-scoped mode works for both families, returning only connected-component mismatches.

JSON validity of `hooks.json` and `marketplace.json` confirmed. `bash -n` on the new hook shell script passed. `validate_frontmatter.py` accepts new UC enum values and the `supersedes:` field on a 3-file fixture (1 shipped, 1 ready successor, 1 superseded).

**Not verified**:

- **End-to-end in a real workspace.** No real UC/decision files exist anywhere under `plugins/` (`find ... -path '*/a4/usecase/*.md'` → empty). First-run exercise of the hook is pending an actual project that uses the plugin.
- **Hook firing under Claude Code.** The `hooks.json` entry is well-formed and `bash -n` passes, but whether the runtime actually invokes it after Write/Edit on matching paths is unverified until a real edit happens.
- **`ready`-gate dialogue flow.** The Step 6 insertion in `/a4:usecase` is written but untested in a real session.

# Rejected alternatives

The user's chat pushback shaped most of these:

- **`shipped → draft` revise verb on `/a4:usecase`.** My first proposal. User countered: "revise가 필요한 경우는 usecase를 새로 만들는게 history관리가 편해 보이는데." Conceded — append-only history via new-UC-with-supersedes is cleaner. No `/a4:usecase revise` exists.
- **Separate `/a4:usecase confirm <id>` command for the draft→ready flip.** Considered, rejected as friction. Folded into the existing `/a4:usecase` wrap-up, matching the pattern where `/a4:plan` Step 2.5 handles shipped confirmation at wrap-up.
- **Auto-flip `draft → ready` when `/a4:usecase` finishes.** Too risky — drafts in progress could be picked up prematurely. Ready-gate requires explicit per-UC user confirmation.
- **Keep `done` and just fix the "directionality" intuition by convention.** Rejected — `done` is ambiguous ("work finished" vs. "system reflects this"), and that ambiguity was precisely what made `done → implementing` feel wrong. Renaming to `shipped` solves the intuition directly.
- **Leave `decision.superseded` and `usecase.superseded` as derived-only (validator-surfaced).** Rejected because the user flagged this as a discoverability problem: "파일에 기록을 안하면 찾기가 힘든 점이 있음." Materialization is the answer.
- **Embed the propagation logic inside `/a4:plan` Step 2.5 (for UC) and `/a4:decision` Step 3 (for decision).** Considered. Rejected by the user in favor of the script+hook approach: "supersedes를 기록하면 반대 superseded를 기록하는 script를 만들어서 status를 기록하는 방법." Benefits confirmed: single source of truth, symmetric across families, works under any edit path (skill, manual, batch), validator-script coverage pair with aligned trigger condition.
- **Add `superseded-by:` as a reverse frontmatter pointer on the old file.** Considered, rejected because it violates the existing `§Relationships are forward-only` convention in the schema doc. The `## Log` back-pointer entry gives the same discoverability without mutating the relationship convention.
- **Cross-family supersedes (e.g., `decision/X supersedes [usecase/Y]`).** Rejected as semantically meaningless in this model. Script explicitly skips; validator would flag any such ref.

# Design principles added (for future sessions)

1. **Materialize whenever a writer is possible.** The session's central design shift. Pure-derived statuses are a design smell unless no writer can be assigned. Before adding a new derived-status enum value, ask: is there an LLM-accessible moment where the trigger condition becomes true? If yes, write it there. If no, the validator path is the fallback.
2. **Writer-validator pair.** For every "derived status with writer", both the writer and the validator must agree on the trigger condition. In this session, both gate on "successor at terminal-active + `supersedes:` non-empty". Drifting the two apart (e.g., validator flagging earlier than the writer flips) creates false positives.
3. **Family-scoped symmetry.** If two families (UC, decision) share a pattern (`supersedes:` → `superseded`), the writer should handle them with one generalized implementation, keyed on a family-to-terminal-active-status table. Resist the urge to write two near-duplicate scripts.
4. **Commit co-location.** Hook-driven cross-file writes (here: target UCs flipped to `superseded`) must land in the same commit as the triggering edit. The hook's `additionalContext` explicitly reminds the session about this so it doesn't accidentally split the edit across commits.
5. **Ready-gate between spec and code.** The `draft → ready → implementing` split is the general pattern for "spec-closed before build-starts" transitions. Any future family that has a similar handoff (e.g., if tasks ever get a `draft` spec phase) should follow the same shape: explicit gate, user confirmation, refusal downstream.

# Plausible follow-ups (not done; user has not requested)

1. **End-to-end test of `propagate_superseded.py` hook in a real workspace.** No real a4/ workspace exists in this repo. First run in a real project should verify: (a) hook fires after `Write` edit, (b) additionalContext surfaces as expected, (c) flipped files end up in the same commit naturally, (d) recovery via `--sweep` works after a `git checkout` discards hook-made changes.
2. **End-to-end test of `/a4:usecase` Step 6 (ready-gate).** The per-UC confirm loop is designed but unexercised. Risk: N-UC sessions could make the loop tedious; if pain surfaces, consider a "batch confirm all" shortcut while preserving per-UC defer.
3. **Migrate existing UC / decision files if any real workspace exists.** No such files in this repo, but downstream users of the plugin may have UCs at `status: done`. A one-off `migrate_done_to_shipped.py` sweep script would help — but only when a real user reports needing it. Not speculative.
4. **ADR for the UC-lifecycle redesign.** The existing spec folder (`plugins/a4/spec/*.decide.md`) captures major a4 design decisions. The UC lifecycle split is ADR-worthy. Not created this session because the schema doc already carries the canonical rules and the handoff captures the rationale; but if the rationale needs to live in a versioned `.decide.md` (e.g., for cross-referencing from `justified_by:` fields on future items), it should be written as a proper ADR.
5. **Consistency validator extension: `supersedes:`-target-type-mismatch.** Current validator skips cross-family refs silently. Could be hardened to flag `usecase X supersedes [decision/Y]` as a schema violation (wrong target type) rather than silently ignoring. Low urgency — `validate_frontmatter.py` already rejects unknown path targets by existence check, and the propagation script logs the skip.
6. **`decision.draft → final` handling.** The `/a4:decision` skill still flips `draft → final` mechanically. If a `final` decision is later found to be wrong (parallel to the UC case), there is currently no `superseded-yourself-by-new-decision` flow via `/a4:decision` either — the user would hand-write the `supersedes:` in the new decision. The hook handles the target flip, so it mostly works, but `/a4:decision` could explicitly suggest "supersede existing decision X?" when the new decision is on a topic that already has a final decision. Not built.
7. **`idea.promoted` and `brainstorm.promoted` materialization.** Same pattern: could follow the same `propagate_*.py` + hook treatment. Both are currently writer-less (only the consistency validator surfaces drift). The preceding handoffs treated this as acceptable; unchanged this session.
8. **`compass` sweep that runs `propagate_superseded.py --sweep`** as part of its housekeeping pass. Covers the "hook didn't fire" gap (e.g., user rebased, hook was skipped). Not urgent — the consistency validator already surfaces any drift at session start.

# Explicitly untouched

- **`validate_body.py`, `drift_detector.py`, `allocate_id.py`, `read_frontmatter.py`, `extract_section.py`, `inject_includes.py`** — none touched.
- **Existing hooks** (`record-edited-a4.sh`, `validate-edited-a4.sh`, `cleanup-edited-a4.sh`, `sweep-old-edited-a4.sh`, `report-status-consistency-session-start.sh`, `report-status-consistency-post-edit.sh`) — unchanged.
- **Skills not in the critical path of UC lifecycle**: `arch`, `compass`, `drift`, `handoff`, `idea`, `index`, `research`, `research-review`, `spark-brainstorm`, `validate`, `web-design-mock` — no changes.
- **Agents other than `task-implementer`, `usecase-reviewer`, `usecase-composer`** — unchanged. Notably `usecase-reviser` was reviewed but found not to need changes: it already handles `blocked` correctly and doesn't write `done`/`shipped`.
- **`/a4:decision` skill body text.** The skill still mentions `draft | final | superseded` in its frontmatter schema block — consistent with the enum, no edit needed. The only implicit change is that `superseded` is now hook-driven rather than "set by hand when a new decision supersedes this one" (as the old schema text said). No active skill change was required because the skill never wrote `superseded` anyway.

# Key files to re-read on the next session

- `plugins/a4/scripts/propagate_superseded.py` — the new writer. Module docstring covers trigger conditions and edge-case handling.
- `plugins/a4/hooks/propagate-superseded.sh` — the PostToolUse hook that drives it.
- `plugins/a4/scripts/validate_status_consistency.py` — generalized validator. See `SUPERSEDES_FAMILIES`, `check_superseded(items, family)`, and the updated module docstring for how it pairs with the script.
- `plugins/a4/references/frontmatter-schema.md` — canonical schema. **§UC lifecycle** subsection (new), **§Status writers** table (rewritten), **§Cross-file status consistency** table (new "Materialized by" column).
- `plugins/a4/skills/usecase/SKILL.md` — **§Wrapping Up Step 6 (Ready-gate)** is the only writer of `draft → ready`.
- `plugins/a4/skills/plan/SKILL.md` — **§Step 2.5: UC ship-review** is the only writer of `implementing → shipped`.
- `plugins/a4/agents/task-implementer.md` — Step 1 is where `ready → implementing` happens and where `draft` gets refused.

# Outstanding parked threads

- `decision-slot-unification` — this thread continues. Writer-assignment is now complete for every UC and decision status value except the two `promoted` values on `idea`/`brainstorm`, which the prior handoff documented as intentionally writer-less. The thread could realistically close with a follow-up session that either (a) materializes `promoted` via a parallel `propagate_promoted.py`, or (b) documents why promoted remains writer-less as a final design decision. Either closes the thread cleanly.
- `a4-redesign`, `experiments-slot`, `idea-slot` — unaffected by this session.
