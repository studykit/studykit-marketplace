---
timestamp: 2026-04-25_0244
topic: a4-hook-automation
previous: 2026-04-25_0205_add-refresh-implemented-by-session-start-hook.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0244. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

This session executed **follow-up #3** from the prior `a4-hook-automation` thread (last snapshot: `plugins/a4/.handoff/a4-hook-automation/2026-04-25_0205_add-refresh-implemented-by-session-start-hook.md`): **overall hook organization cleanup**. Scope covered the prior thread's Task #7 ("`hooks.json` ordering conventions, SessionEnd/Stop symmetric cleanup counterparts, directory-level documentation for `plugins/a4/hooks/`") but ended up broader — the session revealed that the current hooks are mostly duplicate plumbing around `scripts/*.py` calls, and the user chose to **consolidate all non-trivial hook logic into a single Python dispatcher**. The thread topic `a4-hook-automation` is retained.

All implementation work shipped in a single commit: **`a96b690a8`** (`refactor(a4): consolidate hooks into single Python dispatcher`). Plugin version bumped **1.13.0** (was 1.12.0).

# Architectural decision

Seven separate hook files (six bash + one Python) were collapsed into one Python dispatcher. The decision emerged from a six-topic discussion (naming, ordering, lifecycle symmetry, shared helpers, language choice, directory README) whose first three topics fell away once the single-dispatcher direction was chosen.

**Core choice.** The user observed that every non-trivial hook was a wrapper around `scripts/*.py` that re-implemented the same plumbing: parse stdin JSON → check env vars → scope-check `a4/` → shell out to a script → shape output as `additionalContext` / `systemMessage`. Duplicating that plumbing across six bash files was the root cause of the naming/ordering/shared-helper questions. A single Python entry point with subcommand dispatch makes those questions moot.

**Scope refinement.** Not every hook became Python. Three trivial filesystem-op hooks (`cleanup-edited-a4.sh`, `sweep-old-edited-a4.sh`, which remained, and `record-edited-a4.sh`, which did NOT remain — see below) were candidates for staying in bash. The rule settled on: **bash stays for language-independent `rm`/`find` operations; anything that parses JSON, wraps a script, or shapes structured output goes to the Python dispatcher.** By that rule `cleanup` and `sweep` remained bash; `record` moved into the dispatcher because it parses stdin JSON.

**Invocation style.** The user initially accepted a `python3`-direct invocation path (Option B in the discussion) to bypass `uv run` startup overhead on the hot `record` path, then course-corrected to `uv run` to respect the project-wide Python convention (`~/.claude/CLAUDE.md`). All Python hook invocations now go through `uv run`, accepting the ~100–300ms startup per invocation as the cost of convention.

**Structural pattern inside the dispatcher.** Top-level imports are minimal (just `sys`). Each subcommand function imports what it needs locally. The `post-edit` subcommand (fires on every Write/Edit/MultiEdit) benefits most from this; other subcommands follow the same pattern for consistency. This is documented as "fast path" in `hook-conventions.md` §3.

# Ground rules added this session

These codify the design principles agreed during the discussion. All six are now canonically documented in `plugins/a4/references/hook-conventions.md`; summarizing here so the next session can read the handoff alone.

1. **State classification — session-scoped vs permanent workspace state.** A hook writes one or the other. Test: *after a fresh clone and new session, does the state need to already exist?* Yes → permanent (git-tracked). No → session-scoped (typically under `.claude/tmp/`, with `session_id` in the path).
2. **Lifecycle symmetry — two rules depending on state class.**
   - **Rule A (session-scoped):** writer needs a symmetric cleanup at SessionEnd plus a safety-net sweep at SessionStart. Reference implementation: the edit-record family (PostToolUse record → Stop validate → SessionEnd cleanup → SessionStart sweep).
   - **Rule B (permanent reconciliation):** no SessionEnd counterpart; instead the writer must be **idempotent**. Undoing a reconciliation at SessionEnd would actively break the invariant it restores.
3. **Language policy.** Python via `uv run` for anything non-trivial (JSON parse / script wrapper / output shaping). Bash stays for trivial filesystem ops (`rm`, `find ... -delete`).
4. **In-event ordering.** When an event array has multiple entries, order them **write/cleanup → read/report**. Cleanup runs first (so subsequent entries see clean state), then reconciliation writes (so reports see the post-reconciliation state), then read-only reports.
5. **Non-blocking policy.** PostToolUse / SessionStart / SessionEnd always exit 0. Stop may exit 2 on validation violations but exits 0 on any internal failure (missing env, missing scripts, subprocess errors, JSON parse errors, timeouts). Hook bugs must never strand the user.
6. **Output channels — `additionalContext` and `systemMessage` together.** Same payload pattern established in the prior session (the empirical finding that `systemMessage` works on SessionStart despite doc claims). `additionalContext` = LLM-facing, verbose, markdown. `systemMessage` = user-facing, short, one-line. Use both when a hook affects workspace state the user should be aware of; `additionalContext` alone for LLM-only reports; silent-on-clean.

# What got built (commit `a96b690a8`)

## New: `plugins/a4/scripts/a4_hook.py` (~390 lines)

Single dispatcher with three subcommands. Module docstring references `hook-conventions.md`; does not re-state the principles.

- **`post-edit`** — PostToolUse on Write|Edit|MultiEdit. Two-step pipeline: (1) `_record_edited(...)` appends the edited path to `.claude/tmp/a4-edited/a4-edited-<session_id>.txt`; (2) `_report_status_consistency_post(...)` shells out to `validate_status_consistency.py --file <path>` and emits `additionalContext` JSON on rc=2. Fast path: the two stdlib reads happen before any subprocess setup.
- **`stop`** — Stop. Reads the session-scoped record, deduplicates, runs `validate_frontmatter.py` + `validate_body.py` (via `uv run`) on each file. Aggregates violation output to stderr and exits 2 on any violation. `stop_hook_active=true` → silent exit. Missing env/script → stderr warning + exit 0. Cleans up the record file on clean completion.
- **`session-start`** — SessionStart. Runs `_refresh_implemented_by(...)` (write) then `_report_status_consistency_session_start(...)` (read), in that order (§4). Merges their outputs into a single JSON payload: `hookSpecificOutput.additionalContext` concatenates both markdown sections with `\n\n`; top-level `systemMessage` carries the refresh summary (empty if no refresh work).

No third-party dependencies (PEP-723 header declares `dependencies = []`). Subprocess timeouts: 12s for post-edit and session-start script calls (below 15s/20s hook timeouts); 20s per-file for stop validators (well under the 30s hook budget for small N — but see Not verified).

## New: `plugins/a4/references/hook-conventions.md`

Canonical home for the six principles enumerated in Ground rules above. Sections §1 State classification, §2 Lifecycle symmetry (Rule A and B), §3 Language and invocation, §4 In-event ordering, §5 Non-blocking policy, §6 Output channels, §7 Silent-on-clean, and a Non-goals section at the bottom. The dispatcher docstring and `hooks/README.md` both point here.

## New: `plugins/a4/hooks/README.md`

~15-line signpost explaining: only trivial bash hooks live here, Python logic is in `../scripts/a4_hook.py`, design principles are in `../references/hook-conventions.md`. This is the "minimal README" option agreed in Task #6 of the discussion.

## Modified: `plugins/a4/hooks/hooks.json`

Top-level `description` rewritten to describe the new structure. Entries:

- **PostToolUse** (`Write|Edit|MultiEdit`): 1 entry. `uv run a4_hook.py post-edit` (timeout 15s).
- **Stop**: 1 entry. `uv run a4_hook.py stop` (timeout 30s).
- **SessionEnd**: 1 entry. `bash hooks/cleanup-edited-a4.sh` (timeout 5s) — unchanged from prior.
- **SessionStart**: 2 entries. `bash hooks/sweep-old-edited-a4.sh` (5s), then `uv run a4_hook.py session-start` (20s).

Count: 5 entries total, down from 7 previously.

## Deleted

Five obsolete files, absorbed into the dispatcher:

- `hooks/record-edited-a4.sh`
- `hooks/validate-edited-a4.sh`
- `hooks/report-status-consistency-post-edit.sh`
- `hooks/report-status-consistency-session-start.sh`
- `hooks/refresh-implemented-by-session-start.py` (the file added just one session ago)

## Modified: documentation references

- `plugins/a4/README.md` — rewrote the `### Hooks` section's table. Now 5 rows, 3 of which point to `scripts/a4_hook.py` with a subcommand. Added a third flow ("`implemented_by` reconciliation") alongside the existing two (single-file validation, cross-file status consistency). Appended a pointer to `references/hook-conventions.md`.
- `plugins/a4/skills/plan/SKILL.md` line 380 — hook reference updated from `refresh-implemented-by-session-start.py` to `scripts/a4_hook.py session-start`.
- `plugins/a4/references/frontmatter-schema.md` line 363 — same reference update in the §Derived enum table row for `usecase.implemented_by`.
- `.claude-plugin/marketplace.json` — plugin `a4` bumped **1.12.0 → 1.13.0**. No other plugin entries touched.

# Verification performed

Directly in this session (not on a real a4/ workspace):

- **Syntax** — `python3 -m py_compile scripts/a4_hook.py` passes.
- **JSON validity** — `hooks.json` and `marketplace.json` both parse.
- **Silent-skip paths** — all rc=0 with no stdout:
  - post-edit: empty stdin, malformed JSON, non-`a4/` file path
  - stop: empty stdin
  - session-start: no env vars (via `env -i`), no `a4/` directory
- **End-to-end happy path** — fixture at `/tmp/a4-dispatcher-test/` (now deleted):
  - Post-edit: invoked with valid stdin JSON for a `.md` file under a fixture `a4/usecase/`. Exit rc=0. Record file `/tmp/a4-dispatcher-test/.claude/tmp/a4-edited/a4-edited-smoke-sid.txt` was created and contained the edited path.
  - Stop: invoked with matching `session_id`. Read the record, ran `validate_frontmatter.py` on the fixture UC (which had intentionally invalid content — `---` only, no frontmatter). The validator reported `1 violation(s)`; the dispatcher aggregated output to stderr and exited rc=2 — the intended "force Claude retry" behavior.
- **Stale reference scan** — `grep` for the five deleted filenames across `*.md`/`*.py`/`*.sh`/`*.json` outside `.handoff/` shows zero hits. `.handoff/` files retain their historical references (immutable snapshots).

# Not verified

- **Real `a4/` workspace end-to-end.** Still no live workspace in this marketplace repo. Same caveat as every prior a4-hook-automation handoff.
- **Actual rendering of the consolidated SessionStart payload.** The dispatcher's `session-start` subcommand merges refresh's `additionalContext` + `systemMessage` with report's `additionalContext` in a single JSON. This merge is new; the per-piece rendering was verified in the prior session, but the merged payload's behavior in an interactive UI has not been observed.
- **Stop hook 30s budget under load.** Per-file validator cost is `uv run` startup (~100–300ms) × 2 (frontmatter + body), so each file adds roughly 200–600ms of hook time. For a session that edited many files, this can approach or exceed the 30s budget. Not stress-tested.
- **Post-edit hot-path overhead.** Every Write/Edit/MultiEdit on any `.md` file in the project fires `uv run a4_hook.py post-edit`. The fast-path design (lazy imports) mitigates in-process overhead, but `uv run` startup is unavoidable. Subjective impact on edit responsiveness not measured.
- **Subprocess timeout tuning.** 20s per validator call in stop, 12s for other script calls, is a guess. Under slow disk or very large trees, these could be too tight or too generous.
- **Hook-bug surfacing.** The dispatcher is written to stay silent on hard failures (`subprocess.TimeoutExpired`, `FileNotFoundError`, `OSError`, `json.JSONDecodeError`) for non-Stop events. A genuine bug in the dispatcher would therefore be invisible to the user — same policy trade-off called out in the prior session as follow-up #7.

# Rejected alternatives

Ordered by how much discussion they consumed:

- **Keep separate hook files; unify only naming convention.** This was Task #1 of the discussion — e.g., all hooks gain an event suffix (`record-edited-a4-post-edit.sh`, `validate-edited-a4-stop.sh`). Rejected once the user chose single-dispatcher: the naming question becomes moot when there's one file. Recorded because if the dispatcher direction is ever unwound, the remaining files will need a naming rule — the prior handoff's analysis (apply event suffix only to duplicate base names) still stands as the fallback.
- **Mixed-language dispatcher (bash front door with Python subcommands).** Briefly considered: keep bash hooks as thin shells that invoke a Python helper for heavy work. Rejected: the bash plumbing is exactly the duplication the refactor aimed to remove. Moving it into Python is the point.
- **`python3` direct invocation for hot-path `record` only.** Initially accepted (Option D in the discussion). User course-corrected to `uv run` everywhere. Rationale: project-wide Python convention (`~/.claude/CLAUDE.md`) outweighs per-invocation startup cost. The fast-path *internal* pattern (lazy imports) is retained as a code discipline.
- **1-entry per event collapsing everything (including bash `sweep` into Python).** Rejected for SessionStart: trivial `find -delete` gains nothing from Python + uv. Chose the 2-entry layout: bash `sweep` first, then `uv run a4_hook.py session-start` (refresh + report).
- **N-entry per event (preserve current hooks.json structure, just swap bash scripts for `uv run a4_hook.py <subcommand>` calls).** Rejected: would pay `uv run` startup cost per entry (3× per SessionStart, 2× per PostToolUse). The collapse to 1 entry per Python-domain event amortizes that cost.
- **Heartbeat output on clean dispatcher runs.** Rejected (consistent with silent-on-clean in prior session).
- **Per-subtask timeout granularity in `hooks.json`.** Discussed during the 1-entry vs N-entry debate. Rejected: event-level timeout is sufficient; subtask-level budgeting (if ever needed) belongs inside the dispatcher via `subprocess.run(timeout=...)`. Codified as a Non-goal in `hook-conventions.md`.
- **Separate `hooks/README.md` conventions document.** Briefly debated. Rejected: one canonical home for conventions (`references/hook-conventions.md`) avoids sync drift. The `hooks/README.md` exists only as a minimal signpost.

# Follow-ups

Reshaped for the new thread state. The prior handoff's seven follow-ups are carried forward and re-evaluated against the dispatcher architecture.

1. **`transition_status.py --sweep` SessionStart hook.** Deferred again. Now **much simpler to land**: instead of a new sibling file, extend `_session_start()` in the dispatcher with a third step between `_refresh_implemented_by` and `_report_status_consistency_session_start`. Write happens in the middle of the existing write → read ordering. Idempotency (Rule B in conventions) is already required. Ordering within write-phase: refresh first, then sweep (refresh touches UCs' `implemented_by:`; sweep may cascade on supersedes chains — order is conservative, no known dependency).
2. **`compass` wrapper.** Still open. The dispatcher architecture naturally suggests: `compass` becomes a user-facing CLI at `scripts/a4_compass.py` (or similar) that reuses the same subprocess calls the dispatcher makes, but with verbose human-readable output instead of `additionalContext` JSON. Alternative: teach `a4_hook.py` a `--human` flag on each subcommand. First option keeps hook code lean; second avoids duplication. No decision yet.
3. **Upgrade existing status-consistency session-start report to emit `systemMessage`.** Now partially-done — the consolidated payload already gets a `systemMessage` *if refresh produced one*. The status-consistency report alone still only emits `additionalContext`. Optional refinement: when status-consistency reports mismatches but refresh was clean, add a short `systemMessage` like `"N status-consistency mismatch(es) — see context"`. Would require restructuring the merge logic in `_session_start()`; low-stakes.
4. **Observe the consolidated dispatcher in a real workspace.** First production use still pending. Priorities once a live workspace exists: (a) verify the merged SessionStart payload renders correctly, (b) measure post-edit startup overhead subjectively, (c) stress-test Stop budget on an edit-heavy session.
5. **`refresh_implemented_by.py` module docstring.** Still open — the docstring aspirationally refers to "a SessionStart sweep" that now actually exists (and is called from `_refresh_implemented_by` in the dispatcher, not from a dedicated hook file anymore). One-line cleanup.
6. **Hard-fail surfacing design.** Still open. The dispatcher's silent-on-fail policy for non-Stop events means a genuine dispatcher bug (uncaught exception, logic error) would be invisible. Plausible refinement: catch `Exception` at the top of each subcommand and emit a terse stderr note. Tension: stderr on SessionStart might be noisy on the user's terminal depending on Claude Code's rendering. Not urgent.
7. **Test harness for the dispatcher.** New follow-up suggested by this refactor. Current verification was ad-hoc (shell scripts against `/tmp/` fixtures). A proper `tests/` directory with pytest fixtures simulating stdin payloads + fixture `a4/` workspaces would make future dispatcher changes safer. Not scoped for this session.
8. **Stop budget elasticity.** If #4 shows the 30s budget is tight on edit-heavy sessions, options: (a) raise hook timeout, (b) parallelize per-file validator calls inside the dispatcher (`concurrent.futures`), (c) share a single `uv run` process across files via a persistent worker. (c) is the most invasive but also the most impactful — it would require `scripts/validate_frontmatter.py` and `scripts/validate_body.py` to grow a multi-file mode.

# Explicitly untouched

- **`scripts/refresh_implemented_by.py`.** The dispatcher is a pure consumer of its existing `--json` output. The `Report` / `Change` dataclass shapes at lines 45–58 remain the contract.
- **`scripts/validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`.** All called via `uv run` subprocess from the dispatcher. CLI contracts unchanged: `<a4-dir> [<file>]` for the validators, `<a4-dir> [--file <path>]` for status-consistency.
- **`scripts/transition_status.py`.** Single-writer from two sessions ago. Not touched. Relevant to follow-up #1.
- **All other scripts** (`allocate_id.py`, `drift_detector.py`, `extract_section.py`, `inject_includes.py`, `read_frontmatter.py`, `index_refresh.py`).
- **Retained bash hooks.** `hooks/cleanup-edited-a4.sh` and `hooks/sweep-old-edited-a4.sh` — contents unchanged, positions in `hooks.json` unchanged.
- **All agents.** None edited.
- **All skills except `/a4:plan`.** The plan SKILL received a one-line hook reference update; all other skill SKILL.md files are untouched.
- **All other plugins in the marketplace.** Only `a4` edited.
- **Prior-thread handoffs.** Still point-in-time snapshots.
- **`spec/*.decide.md` files.** Untouched.

# Key files to re-read on the next session

- `plugins/a4/scripts/a4_hook.py` — the dispatcher. Read top-to-bottom before extending (e.g., to add follow-up #1's `--sweep` step). Pay attention to the fast-path / lazy-import pattern and the shared helpers (`_emit`, `_unlink_silent`, `_run_validator`).
- `plugins/a4/references/hook-conventions.md` — the authoritative design doc. Required reading before designing any new hook. If a new design *breaks* one of the six principles, update this doc as part of the change.
- `plugins/a4/hooks/hooks.json` — event wiring + top-level description. The description documents the architecture at a high level; keep it accurate if the structure shifts.
- `plugins/a4/hooks/README.md` — signpost only. Update only if the bash-vs-Python split changes.
- `plugins/a4/scripts/refresh_implemented_by.py` — unchanged, but the dispatcher's `_refresh_implemented_by(...)` depends on its `Report` / `Change` JSON shape.
- `plugins/a4/scripts/validate_status_consistency.py` — unchanged, CLI depended on.
- `plugins/a4/.handoff/a4-hook-automation/2026-04-25_0205_...md` (the prior handoff) — contains the `systemMessage`-works-on-SessionStart empirical finding and the detailed write-on-SessionStart policy debate. Still relevant context.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Live follow-ups are #1 (deferred `--sweep` hook extension), #2 (`compass` wrapper), #3 (SessionStart `systemMessage` extension), #5 (docstring cleanup), #6 (hard-fail surfacing), #7 (test harness), #8 (Stop budget elasticity).
- **`uc-status-transition-system`** — formally concluded; still carries two minor parked items: tighter `## Section` substring checks and body-section drift validator for `final` decisions. Neither commissioned.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open from the status-transition thread's follow-up #5. Leading proposal: add a `promote` mode to `/a4:idea` and `/a4:spark-brainstorm`. Unrelated to this thread.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected by this session.
