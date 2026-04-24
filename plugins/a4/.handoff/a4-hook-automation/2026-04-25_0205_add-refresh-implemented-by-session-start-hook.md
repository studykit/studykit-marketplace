---
timestamp: 2026-04-25_0205
topic: a4-hook-automation
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0205. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

This session executed **follow-up #2** from the prior `uc-status-transition-system` thread (last snapshot: `plugins/a4/.handoff/uc-status-transition-system/2026-04-25_0122_migrate-decision-family.md`): **add a `SessionStart` hook for `refresh_implemented_by.py`**.

Scope was deliberately narrow:

- A single new SessionStart hook that reconciles UC `implemented_by:` reverse-link drift at session entry.
- No `transition_status.py --sweep` bundling (explicitly deferred — see Rejected alternatives).
- No other follow-ups from the prior thread.
- No other automation, agent, or skill changes outside the one-line update needed in `/a4:plan` and the table-cell update in `frontmatter-schema.md`.

The thread this handoff opens — `a4-hook-automation` — is new. Future sessions that revisit hook ordering, add the deferred `--sweep` hook, design the `compass` wrapper, or perform a broader hook-organization cleanup should chain into this topic rather than reopening `uc-status-transition-system`.

All implementation work shipped in a single commit: **`7860fbf57`** (`feat(a4): refresh implemented_by on SessionStart via hook`). Plugin version bumped **1.12.0** (was 1.11.0 from the prior session).

# Ground rules added this session

These are new; they do not modify any rule from the prior thread.

- **Write-on-SessionStart is legitimate for deterministic recomputations of auto-maintained fields.** A SessionStart hook is allowed to modify workspace `.md` files when (a) the write is a pure deterministic recomputation (same inputs → same output), (b) the field is declared auto-maintained with hand-edits forbidden (e.g., `usecase.implemented_by`, per `references/frontmatter-schema.md` line 151: *"never hand-write"*), and (c) the hook surfaces the changes transparently via `systemMessage`. For anything else — fields the user authors, non-deterministic transformations, or silent writes without surfacing — SessionStart is the wrong event. This is a narrower license than the prior "single writer" rule, not a broader one: it only applies to fields that are already, by prior decree, outside the user's authoring surface.
- **Silent-on-clean is the convention for SessionStart hooks.** When a hook finds no drift, emit nothing — no heartbeat, no "ran successfully" message. Matches the existing `report-status-consistency-session-start.sh`. Session entry is a high-attention moment; reserve visible output for actionable news.
- **Non-blocking is mandatory on SessionStart.** All SessionStart hooks exit 0, even on internal failure. A failed hook must not block session entry. Hard failures (subprocess error, JSON parse error, missing script) are silent; only meaningful drift/errors surface.
- **SessionStart hook output uses both channels deliberately.** `hookSpecificOutput.additionalContext` (LLM-facing, verbose, markdown-structured) and top-level `systemMessage` (user-facing, short, one-liner) coexist in a single JSON payload. Use both when the work affects workspace state the user should be aware of. `systemMessage` alone is under-informative for the LLM; `additionalContext` alone leaves the user blind.

# What got built (commit `7860fbf57`)

## New file: `plugins/a4/hooks/refresh-implemented-by-session-start.py`

Python SessionStart hook, ~135 lines. Responsibilities:

- Silent-skip if `CLAUDE_PROJECT_DIR` or `CLAUDE_PLUGIN_ROOT` is unset.
- Silent-skip if `${CLAUDE_PROJECT_DIR}/a4` does not exist or is not a directory.
- Silent-skip if `scripts/refresh_implemented_by.py` is missing (defensive).
- Shells out: `uv run <script> <a4-dir> --json`, 12s subprocess timeout (2s below the hook timeout in `hooks.json`).
- On subprocess timeout / exec error / non-zero rc / JSON parse error: silent exit 0 (hard-fail policy).
- On valid JSON report:
  - Clean (`changes == [] and errors == []`): silent exit 0.
  - Changed or partial-error: emit `{hookSpecificOutput: {hookEventName, additionalContext}, systemMessage}` on stdout, exit 0.
- `systemMessage` format: `refreshed implemented_by on N UC(s)` / `refreshed implemented_by on N UC(s), M error(s) — see context` / `M error(s) — see context`.
- `additionalContext` format: markdown section `## a4/ implemented_by refresh (SessionStart)` with per-UC diffs rendered as `` - `usecase/<id>`: `[prev]` → `[new]` `` and errors listed below, plus a trailing sentence reminding the reader that `implemented_by:` is auto-maintained.

No dependencies (empty `dependencies = []` in the PEP-723 script block). Relies only on stdlib.

## Modified: `plugins/a4/hooks/hooks.json`

- **`SessionStart` array reordered and extended.** New order (top to bottom):
  1. `sweep-old-edited-a4.sh` (5s, unchanged) — orphan record file cleanup.
  2. **[NEW]** `refresh-implemented-by-session-start.py` (15s) — the new hook.
  3. `report-status-consistency-session-start.sh` (15s, moved from position 2) — status-consistency reporter. Moved to last so its report runs over the state after reverse-link drift is healed.
- **Top-level `description` field extended.** Mentions the new SessionStart responsibility: *"On SessionStart, also refresh UC `implemented_by:` reverse-links via `scripts/refresh_implemented_by.py` so drift from cross-branch edits or manual task edits is reconciled before work begins."*

## Modified: `plugins/a4/references/frontmatter-schema.md` (table row at line 363)

The `usecase.implemented_by` row in the §Derived enum values table was overstating reality: it said the refresh is *"called at end of `/a4:plan` Phase 1 and on session-start sweep"* when in fact no session-start mechanism existed. Updated to name the actual hook: *"called at end of `/a4:plan` Phase 1 and from the `refresh-implemented-by-session-start.py` SessionStart hook."*

## Modified: `plugins/a4/skills/plan/SKILL.md` (line 380)

Previously a recommendation to the reader: *"Run `scripts/refresh_implemented_by.py` at session start too..."* — a standing instruction to do something manual. Rewritten to state the hook exists and does this automatically: *"`scripts/refresh_implemented_by.py` also runs automatically via the `refresh-implemented-by-session-start.py` SessionStart hook (see `hooks/hooks.json`) to catch any task-file changes that happened on other branches."*

## Modified: `.claude-plugin/marketplace.json`

Plugin `a4` version bumped **1.11.0 → 1.12.0**. No other plugin entries touched.

# Key technical finding — `systemMessage` on SessionStart (contrary to public docs)

The session surfaced a documentation/reality gap that is worth preserving for future hook work.

**Claim under test:** the Claude Code documentation implies that SessionStart hooks support only `hookSpecificOutput.additionalContext` and not `systemMessage`. The `claude-code-guide` subagent consulted early in the session asserted this explicitly (citing https://code.claude.com/docs/en/hooks and https://code.claude.com/docs/en/hooks-guide).

**Empirical contradiction:**

1. A working production example exists in another marketplace: `~/.claude/plugins/marketplaces/claude-code-warp/plugins/warp/scripts/on-session-start.sh` — a SessionStart hook that emits `{"systemMessage": "..."}` and nothing else.
2. The official `plugin-dev/skills/hook-development/SKILL.md` (in the `claude-plugins-official` marketplace) documents `systemMessage` as a top-level hook output field alongside `hookSpecificOutput` for multiple events.
3. A minimal empirical probe (set up under `/tmp/sm-probe/`, now deleted) confirmed user-visible rendering: a SessionStart hook that emits both `hookSpecificOutput.additionalContext` and top-level `systemMessage` in the same JSON payload had its `systemMessage` rendered in the interactive UI as **`SessionStart:<hook-name> says: <systemMessage>`** — visible to the user above the prompt — while `additionalContext` was injected into the LLM's context (verified by prompting the LLM via `claude --print` and observing it echo back the additionalContext token).

**Implication for hook design:** a SessionStart hook can produce both LLM-targeted context and a user-visible notification in a single JSON payload. This is the pattern adopted in the new hook. It is also the pattern that a future hook (e.g., a `transition_status.py --sweep` hook) should adopt when it lands.

**Implication for existing hooks:** `plugins/a4/hooks/report-status-consistency-session-start.sh` only uses `additionalContext`. It could optionally be upgraded to also surface a short `systemMessage` when mismatches are found. Not done this session; filed under follow-ups.

# Verification performed

Using an ephemeral fixture at `/tmp/a4-hook-test/` (now deleted):

- **Clean run (no drift):** hook exits 0 with empty stdout. Confirmed by fresh `implemented_by: [task/201-login-form]` on the UC file and empty output.
- **Drift run:** UC with `implemented_by: []` and a task with `implements: [usecase/001-login]` — hook emits expected JSON, `systemMessage` reads `refreshed implemented_by on 1 UC(s)`, `additionalContext` contains the per-UC diff, and the UC file is physically modified to `implemented_by: [task/201-login-form]`.
- **Idempotent re-run:** second invocation against the just-healed fixture is silent (exit 0, no stdout).
- **Missing workspace:** `CLAUDE_PROJECT_DIR` pointing at a directory without `a4/` → silent exit 0.
- **Missing env:** `CLAUDE_PROJECT_DIR` unset → silent exit 0.
- **JSON validity:** `hooks.json` and `.claude-plugin/marketplace.json` both parse.
- **SessionStart array order:** confirmed via `python3 -c "import json; ..."` — output was `Sweep orphan... / Refresh UC implemented_by... / Report cross-file status-consistency...`.
- **SessionStart `systemMessage` visibility:** empirically confirmed via an earlier independent probe (separate fixture) — the user visually confirmed `SessionStart:startup says: PROBE_SYSMSG_TOKEN=sys_xyz789_visible_to_user` rendered in their interactive UI.

# Not verified

- **Real `a4/` workspace end-to-end.** Still no live workspace under `plugins/` — same caveat as every prior handoff in this marketplace. First production exercise of the new hook awaits a project that actually has an `a4/` directory in `CLAUDE_PROJECT_DIR`.
- **Interactive UI render of the new hook's actual `systemMessage`.** The generic `systemMessage` mechanism is confirmed; the specific string produced by *this* hook has not been observed in a real session. Visible in-session test requires opening a fresh Claude Code session under a directory that has an `a4/` workspace with real drift — simple but not done this session.
- **Timeout margin on large workspaces.** 15s hook timeout minus 12s subprocess timeout leaves 3s of slack for Python startup and hook I/O. Not stress-tested against very large task trees (hundreds of files).
- **Hard-fail surfacing.** The hook is coded to be silent on subprocess failures (non-blocking policy). Not exercised against a genuinely broken `refresh_implemented_by.py` or a corrupted UC file.
- **Interaction with unstaged working-tree state.** The hook writes files on session entry. If the user had unstaged edits on a UC file, the hook's `implemented_by:` rewrite would coexist with them. Theoretically fine (YAML frontmatter edit, not a body edit) but not exercised.

# Rejected alternatives

Ordered by how much discussion they consumed:

- **Bundle `transition_status.py --sweep` into the same SessionStart hook.** Considered, then dropped. Reasons: (1) separate drift axis — `refresh_implemented_by` handles task↔UC reverse links, `--sweep` handles supersedes chains; (2) clearer minimal-change diff for this session; (3) `--sweep` naturally belongs in the `compass` wrapper design (prior handoff follow-up #6) which treats it as one of several validators; (4) keeps the "write-on-SessionStart" policy debate scoped to a single new hook for this session. Outcome: `--sweep` remains a future follow-up, tracked on this thread.
- **Two-hook split (refresh hook + sweep hook) vs single combined hook.** Implicitly chosen during ordering design: separate hooks in `hooks.json` give each its own timeout, failure domain, and visual identity in the hook list. Same reasoning used for the existing status-consistency reporter remaining separate from the edit-record sweeper.
- **Dry-run + advisory only (Option 2 on the write-policy question).** Hook would run `--dry-run --json` and only report drift via `systemMessage` + `additionalContext`, deferring the actual write to an explicit LLM or user action. Rejected because LLM follow-through on "please run X" is unreliable — drift would persist across sessions, defeating the motivation. The auto-maintained nature of `implemented_by:` (user hand-edits are forbidden by schema) means there's no user-consent concern to protect.
- **Heartbeat output on clean runs** (e.g., `implemented_by: clean (N UCs scanned)`). Rejected — would violate the silent-on-clean convention the other hooks follow, and every session would open with a pointless status line.
- **Git-cleanliness guard before writing** — skip the hook's write if the working tree is dirty, to avoid entangling the refresh with unstaged user edits. Rejected as over-engineering: users routinely open sessions with unstaged edits, and the `implemented_by:` rewrite is a single-line YAML edit that a reader can immediately identify in `git diff`. The entanglement, if it happens, is trivially unwound.
- **Bash wrapper (consistent with existing four bash hooks) vs Python.** Chose Python. The `refresh_implemented_by.py` script already emits a structured JSON report; parsing that in bash via `jq` to reshape into the final hook output JSON is error-prone. Python stdlib handles it cleanly in ~30 lines of real logic.
- **Indirect `systemMessage` emulation via `additionalContext`** ("inject a line into LLM context telling it to announce the refresh to the user"). Briefly proposed as the only available path when the doc claimed `systemMessage` was unsupported on SessionStart. Superseded by the empirical finding that direct `systemMessage` works.
- **Reuse topic `uc-status-transition-system` for this handoff.** Considered because the session executed that thread's follow-up #2. Rejected: the thread scope ("status transitions through a single writer") is distinct from this session's scope (reverse-link refresh automation via SessionStart hook). Future hook-automation work — `--sweep` hook, `compass` wrapper, overall hook-layout cleanup — is the natural continuation of *this* session, not of the status-transition thread. Hence new topic `a4-hook-automation`.

# Plausible follow-ups

Fresh list scoped to this thread. Items #1 and #3–#7 are genuinely new; #2 is carried over from the prior thread's follow-up #6.

1. **`transition_status.py --sweep` as SessionStart hook.** Deferred this session. The expected shape: a sibling Python hook (`sweep-supersedes-session-start.py`?) that runs `transition_status.py --sweep --json`, reports cascades performed in `systemMessage` + `additionalContext`. Order in `hooks.json`: between the new refresh hook and `report-status-consistency-session-start.sh`. Same output policy (silent-on-clean, both channels on work).
2. **`compass` wrapper.** The prior handoff's follow-up #6. Now naturally chains into this thread: `compass` should call `refresh_implemented_by.py --sweep`, `transition_status.py --sweep`, and the existing validators in one user-invoked command. Overlaps with #1: once the `--sweep` hook lands, `compass` effectively becomes the on-demand equivalent of what SessionStart does automatically.
3. **Task #7: overall hook organization cleanup.** Recorded as a deliberate future task during this session. Topics to revisit once a few more hooks accumulate: `hooks.json` ordering conventions, whether SessionEnd/Stop need symmetric cleanup counterparts for each SessionStart write, directory-level documentation for `plugins/a4/hooks/`.
4. **Upgrade `report-status-consistency-session-start.sh` to also emit `systemMessage`.** With the new empirical knowledge that `systemMessage` works on SessionStart, the existing consistency hook could surface a short user-visible summary ("3 status consistency mismatches — see context") alongside its full `additionalContext` report. Low effort, improves visibility of an otherwise LLM-only signal.
5. **Observe the new hook in a real workspace.** First production use will both validate the rendered `systemMessage` format and exercise the timeout margin. Until then the hook is well-tested on synthetic fixtures only.
6. **`refresh_implemented_by.py` docstring still references session-start sweep in aspirational terms.** Module docstring (line ~22) says *"A SessionStart sweep is also useful after a `git checkout` or branch rebase."* Now that the hook exists, this could be updated to state fact rather than suggestion: *"The `refresh-implemented-by-session-start.py` hook runs this at every session start."* One-line cleanup; not done this session to keep the commit diff focused on hook wiring.
7. **Hard-fail surfacing design.** Current policy is "silent on hard fail" (defensive: never block session entry). A plausible refinement: when the hook itself hits a genuine bug — not a subprocess timeout, not a parse error, but something like an uncaught Python exception — surface a terse `systemMessage` like *"refresh_implemented_by hook errored — check debug log"*. Requires choosing when silence becomes counterproductive. Not a current pain point.

# Explicitly untouched

- **`scripts/refresh_implemented_by.py` itself.** No code change; the hook is a pure consumer of its existing `--json` output shape. The script's `Report` / `Change` dataclass shapes (see lines 45–58) are an API contract the hook depends on.
- **`scripts/transition_status.py`.** Single-writer from the prior session — not modified here.
- **All other scripts** (`allocate_id.py`, `drift_detector.py`, `extract_section.py`, `inject_includes.py`, `read_frontmatter.py`, `validate_body.py`, `validate_frontmatter.py`, `validate_status_consistency.py`, `index_refresh.py`).
- **All other hooks.** `record-edited-a4.sh`, `report-status-consistency-post-edit.sh`, `validate-edited-a4.sh`, `cleanup-edited-a4.sh`, `sweep-old-edited-a4.sh`, `report-status-consistency-session-start.sh` — the last one only moved position in `hooks.json`; its script contents are unchanged.
- **All skills except `/a4:plan`** (one-line prose change). `/a4:decision`, `/a4:usecase`, `/a4:task`, `/a4:review`, `/a4:idea`, `/a4:spark-brainstorm`, `/a4:auto-usecase`, `/a4:spark-discuss` — not touched.
- **All agents.** None edited.
- **Prior-thread handoffs.** Still point-in-time snapshots; not edited.
- **`spec/*.decide.md` files.** Untouched.
- **All other plugins in the marketplace.** Only `a4` edited.

# Key files to re-read on the next session

- `plugins/a4/hooks/refresh-implemented-by-session-start.py` — the new hook. Read top-to-bottom. Understand the output shape before designing a sibling hook for `transition_status.py --sweep`.
- `plugins/a4/hooks/hooks.json` — SessionStart array layout + updated top-level `description`.
- `plugins/a4/scripts/refresh_implemented_by.py` — unchanged, but the hook depends on its `Report` / `Change` JSON shape. Read lines 45–58 and lines 1–35 (docstring).
- `plugins/a4/references/frontmatter-schema.md` line 363 (§Derived enum table row for `usecase.implemented_by`) — the row was updated; the surrounding table conventions still apply to future new rows.
- `plugins/a4/skills/plan/SKILL.md` line 380 — one-line prose change.
- `~/.claude/plugins/marketplaces/claude-code-warp/plugins/warp/scripts/on-session-start.sh` — external reference for a working `systemMessage`-on-SessionStart example. Useful cross-check if future doc audits claim the field is unsupported.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Direct extensions: deferred `--sweep` hook (follow-up #1), `compass` wrapper (#2), hook-layout cleanup (#3), consistency-hook `systemMessage` upgrade (#4).
- **`uc-status-transition-system`** — formally concluded, informally still carrying two minor parked items from its last handoff: (a) tightening `## Section` substring checks to line-anchored regex, (b) validator for body-section drift on already-`final` decisions. Both remain optional; neither is commissioned.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open from the status-transition thread's follow-up #5. Leading proposal: add a `promote` mode to `/a4:idea` and `/a4:spark-brainstorm`. Unrelated to this thread.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected by this session.
