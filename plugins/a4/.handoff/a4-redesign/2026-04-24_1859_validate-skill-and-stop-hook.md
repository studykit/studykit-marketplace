---
timestamp: 2026-04-24_1859
topic: a4-redesign
previous: 2026-04-24_1813_topic-folder-layout.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-24_1859. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Handoff: `/a4:validate` skill + Stop-hook session validation — `a4-redesign` thread closed

Topic thread: `a4-redesign`. This is the thread-closure handoff anticipated by `2026-04-24_1813_topic-folder-layout.md` ("After Compass lands, a thread-closure handoff on `a4-redesign` becomes appropriate"). All 13 ADR Next Steps from `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` are now `[x]`. No new thread is queued.

## Pre-handoff commits

- **`4ca34820f`** — `feat(a4): add /a4:validate skill and close compass-redesign ADR item`. 4 files; new `plugins/a4/skills/validate/SKILL.md`, README skills-table entry, marketplace.json a4 1.0.2 → 1.1.0, ADR Next Step 8 flipped `[ ]` → `[x]` with a detailed completion note that also records the validator-split rationale.
- **`3a6ea40d2`** — `feat(a4): add Stop-hook session validation for a4/ edits`. 7 files; new `plugins/a4/hooks/` with 4 bash scripts + `hooks.json`, README Hooks section, marketplace.json 1.1.0 → 1.1.1.

Working tree was clean at the start of this handoff — nothing else to bundle into a pre-handoff commit.

## Primary read for next session

If the next session needs context on anything this session touched:

1. **`plugins/a4/skills/validate/SKILL.md`** — the new `/a4:validate` skill. `disable-model-invocation: true`; user-triggered only. Runs `validate_frontmatter.py` + `validate_body.py` against `<project-root>/a4/` and reports both results verbatim.
2. **`plugins/a4/hooks/`** — `hooks.json` + 4 scripts implementing the accumulate-then-validate pattern. Load order: `record-edited-a4.sh` (PostToolUse) → `validate-edited-a4.sh` (Stop) → `cleanup-edited-a4.sh` (SessionEnd) → `sweep-old-edited-a4.sh` (SessionStart).
3. **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the ADR. All 13 Next Steps now `[x]`. Step 8 (Compass redesign)'s completion note is the load-bearing one for this session — it captures the validator-split rationale and points at `plugins/a4/skills/validate/SKILL.md`.
4. **`plugins/a4/README.md`** — Components section now lists `validate` skill and a new **Hooks** section documenting the 4-stage pattern.
5. This handoff.

## Scope of the pre-action discussion

Two design decisions were made before writing code. Both are recorded here so the next session doesn't relitigate.

### 1. Validator-split: `/a4:validate` as its own skill, NOT wired into compass

The prior handoff left it as a design choice:

> Consider wiring `validate_frontmatter.py` and `validate_body.py` into Step 3 — they surface a different class of inconsistency (schema / body-convention) that a compass pass could reasonably report. Alternatively, leave them for a potential future `/a4:validate` skill.

Resolved: **leave them out of compass; create `/a4:validate`.** Reasons:

- Compass's scope is strategic navigation ("where am I, what next"). Validators are tactical correctness (`exit 2` style strict checks). Mixing noise classes dilutes both.
- `/a4:validate` as a standalone skill is reusable from pre-commit hooks and CI — not possible if logic is trapped inside compass.
- `drift_detector.py` already covers cross-session wiki↔issue drift from inside compass; validators cover a different class (schema / body convention) that pairs more naturally with user-initiated checks.

The compass SKILL.md itself was **not** re-edited this session. It had already been rewritten for the wiki+issue layout in commit `72f62ac24` from an earlier same-day session. The handoff from 2026-04-24_1813 claimed compass still used the pre-ADR topic × stage grid — that claim was stale. Verified by reading the current `plugins/a4/skills/compass/SKILL.md`: Step 0 runs `index_refresh.py`, Step 1.1 resolves integer id / folder-qualified path / wiki basename / free-text / empty, Step 3.1 invokes `drift_detector.py`, Step 3.3 diagnoses via six layers (workspace foundation → wiki foundation → drift alerts → non-drift reviews → active tasks → blocked items → completion), Step 3.5 per-item archive. ADR-aligned in full.

Because compass was already aligned, Step 8's [x] in the ADR is primarily a bookkeeping correction — the substantive rewrite had shipped in `72f62ac24`, and this session only added the validator-split decision and the new skill.

### 2. Stop-hook pattern: accumulate-then-validate, adapted from Knowledge

Initial implementation (scrapped mid-session) used transcript-parsing: the Stop hook read the `transcript_path` JSONL, walked entries after the last real user message, and looked for `Edit`/`Write`/`MultiEdit`/`NotebookEdit` tool uses with `file_path` under `<project-root>/a4/`. This "per-turn only" guard was correct but missed the multi-turn case (edit in turn 1, unrelated work in turn 2, Stop hook skips in turn 2 even though violations still exist).

User pointed to `/Users/myungo/Kakao/Knowledge/.claude/hooks/` as the reference pattern. Four scripts there: `record-edited-md.sh` (PostToolUse), `lint-edited-md.sh` (Stop), `cleanup-edited.sh` (SessionEnd), `sweep-old-edited.sh` (SessionStart). Session-scoped record file at `$project/.claude/tmp/edited/md-edited-<session_id>.txt` accumulates across the session; lint on Stop drains the record.

Adopted fully. The a4 variant mirrors the structure but uses:

- Record directory `.claude/tmp/a4-edited/` and filename `a4-edited-<session_id>.txt` (namespace hygiene; Knowledge and a4 workspaces may coexist in one project).
- Record filter: `$file_path` must sit under `$project/a4/` (Knowledge filtered away `.claude/` — we filter **into** `a4/` instead).
- Validator invocation: loops through recorded files and calls `validate_frontmatter.py` / `validate_body.py` with the file as the optional positional (single-file mode). **Workspace-wide id-uniqueness is intentionally skipped** — single-file mode disables that check in `validate_frontmatter.py`. It stays `/a4:validate`'s responsibility. Rationale: the hook should not surface violations in files the user did not touch this session; id-uniqueness across files necessarily requires reading all of them, which would re-report legacy violations.

**Blocking behavior.** On violations, `exit 2` with stderr — Claude Code re-runs the agent loop with the stderr as feedback, causing Claude to attempt a fix next turn. `stop_hook_active: true` short-circuits to `exit 0` silently to prevent tight retry loops. Internal errors (missing validator scripts, unexpected return codes) fall back to `exit 0` with a warning on stderr — never block Stop on hook bugs. On clean, the record file is **deleted** (so subsequent Stops without new edits are silent); on violations, the record file **persists** (the next Stop will re-validate and either clean or keep blocking).

## What this session accomplished

### Change 1 — `plugins/a4/skills/validate/SKILL.md` (new)

- `disable-model-invocation: true` — user must type `/a4:validate` explicitly; never triggered by agent routing.
- `allowed-tools: Bash, Read`.
- `argument-hint: "[file] [--json]"` — both pass through to the underlying scripts.
- Step 1: resolve project root via `git rev-parse --show-toplevel`, abort if `a4/` missing.
- Step 2: `uv run "${CLAUDE_PLUGIN_ROOT}/scripts/validate_frontmatter.py" "$ROOT/a4" $ARGUMENTS`.
- Step 3: same for `validate_body.py`.
- Step 4: relay each validator's output verbatim, clearly labelled (`=== frontmatter ===` / `=== body ===`), do not suppress one set on the other's success. Aggregate status is one of four branches (both clean / frontmatter only / body only / both).
- Step 5: never auto-fix. Cluster analysis: if many violations hit one file, suggest the iteration skill that owns the target. For id uniqueness, point at `scripts/allocate_id.py`.
- Non-goals spelled out: no auto-fix, no drift detector invocation, no INDEX refresh, no commit, no model-invocation.

### Change 2 — `plugins/a4/hooks/` (new, 5 files)

Pattern adapted from `/Users/myungo/Kakao/Knowledge/.claude/hooks/`. All scripts are bash + `jq`, matching that pattern's simplicity (Python was the first-cut approach for the scrapped transcript-parser; bash is the right tool here).

**`hooks.json`** — registers 4 event handlers: PostToolUse (matcher `Write|Edit|MultiEdit`), Stop, SessionEnd, SessionStart.

**`record-edited-a4.sh`** — PostToolUse:

- Reads stdin JSON, extracts `tool_name`, `tool_input.file_path`, `session_id`.
- Requires all three present; bails silently otherwise.
- Keeps only `Write|Edit|MultiEdit`; skips other tools.
- Requires `.md` suffix and absolute path under `$CLAUDE_PROJECT_DIR/a4/`.
- Appends to `$CLAUDE_PROJECT_DIR/.claude/tmp/a4-edited/a4-edited-<session_id>.txt`.
- Always `exit 0`.

**`validate-edited-a4.sh`** — Stop:

- Reads stdin JSON for `session_id` + `stop_hook_active`.
- `stop_hook_active: true` → `exit 0` (loop prevention).
- Missing record file → `exit 0`.
- Collects unique still-existing files under `$a4_dir/` from the record (filters race-deleted and out-of-scope lines).
- For each collected file, runs `uv run $fm_script $a4_dir $file` and `uv run $body_script $a4_dir $file`; expects rc 0 (clean) or 2 (violations). Any other rc is treated as internal error and the hook bails with `exit 0` + stderr warning.
- Aggregates stdout+stderr from each failing validator into `fm_output` / `body_output`.
- If both are clean: delete the record file, `exit 0`.
- If either has violations: write a combined report to stderr with header "a4/ validators found issues in files edited this session:" + per-validator sections + trailer pointing at the reference docs and `/a4:validate`, then `exit 2`. Record file is **kept** so the next Stop re-validates.

**`cleanup-edited-a4.sh`** — SessionEnd: `rm -f` the session's record file. Always `exit 0`.

**`sweep-old-edited-a4.sh`** — SessionStart: `find $record_dir -type f -name 'a4-edited-*.txt' -mtime +1 -delete`. Covers crashed sessions where SessionEnd never ran. Always `exit 0`.

### Change 3 — `plugins/a4/README.md` (modified)

- Skills table: added `validate` row.
- **New Hooks section** documenting the 4-stage pattern with per-event purpose table.
- Scope sentence clarifying that only files under `$project/a4/` are recorded and pre-existing violations in untouched files are intentionally not surfaced — deferred to the user-triggered `/a4:validate`.

### Change 4 — `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` (modified)

ADR Next Step 8 (Compass redesign): `[ ]` → `[x]` with a multi-paragraph completion note covering:

- The already-landed compass rewrite (cites commit `72f62ac24` and lists the seven structural changes).
- The deliberate non-integration of validators into compass ("surface a different class of inconsistency best exposed via a dedicated `/a4:validate` skill that can also be called from pre-commit hooks or CI").
- The new `/a4:validate` skill wrapping both validators.

### Change 5 — `.claude-plugin/marketplace.json` (modified)

a4 plugin version trajectory this session:

- `1.0.2` → `1.1.0` in commit `4ca34820f`. **Minor** bump — a new user-facing skill (`/a4:validate`) is feature-additive.
- `1.1.0` → `1.1.1` in commit `3a6ea40d2`. **Patch** bump — the Stop-hook bundle is behavior-additive but strictly wrapping existing validator logic; no new user-facing commands.

### diff stat (aggregate across both commits)

```
 .claude-plugin/marketplace.json                                 |   4 +-
 plugins/a4/README.md                                            |  14 ++
 plugins/a4/hooks/cleanup-edited-a4.sh                           |  19 ++
 plugins/a4/hooks/hooks.json                                     |  47 +++++
 plugins/a4/hooks/record-edited-a4.sh                            |  39 ++++
 plugins/a4/hooks/sweep-old-edited-a4.sh                         |  15 ++
 plugins/a4/hooks/validate-edited-a4.sh                          | 108 +++++++++++
 plugins/a4/skills/validate/SKILL.md                             |  81 +++++++++
 plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md    |   2 +-
 9 files changed, 327 insertions(+), 2 deletions(-)
```

## Design decisions worth flagging

Record here so the next session doesn't relitigate.

1. **Validators NOT wired into compass.** Resolved in favor of a standalone `/a4:validate` skill + a Stop-hook invoker. Both operate on the same `validate_frontmatter.py` / `validate_body.py` libraries; compass stays a pure navigation skill. Rationale: compass's output is strategic (what skill next); validators' output is tactical (schema/convention violations, exit-2-on-failure style). Mixing degrades both. `/a4:validate` also makes the validators reusable from pre-commit and CI.
2. **Stop hook blocks with `exit 2`, not passive `additionalContext`.** Initial draft used a JSON `hookSpecificOutput.additionalContext` emission (non-blocking, surfaced at next prompt). Replaced with Knowledge's `exit 2 + stderr` pattern because the validators report ground-truth workspace correctness — leaving violations floating risks accumulated decay. Claude retries with the feedback; `stop_hook_active` prevents loops; internal errors fall back to `exit 0` so hook bugs never block Stop.
3. **Hook scope = session-edited files only.** Workspace-wide checks (id uniqueness) are deferred to `/a4:validate`. Rationale: the hook should not harass the user about pre-existing violations in files they did not touch. Legacy workspaces would otherwise block every Stop indefinitely. The trade-off is that cross-file issues (id collision, missing wiki page, etc.) are only caught on manual `/a4:validate` or when `drift_detector.py` runs (via compass Step 3.1 or `/a4:drift`).
4. **Validators invoked in single-file mode, not whole-workspace mode.** Follows from (3). `validate_frontmatter.py` has an explicit `if not args.file: validate_id_uniqueness(a4_dir)` guard that disables id-uniqueness in single-file mode — that is the exact desired behavior.
5. **Bash + `jq` for hooks, not Python.** The scrapped first-cut used Python with transcript parsing. Bash is the right tool for record-and-loop — matches Knowledge's pattern, no stdlib dependencies, no `uv run` overhead on the record hook (which fires on every tool use). Validator invocation from the Stop script still uses `uv run` because that is how the Python scripts run.
6. **`CLAUDE_PROJECT_DIR` env var, not payload `cwd` + git rev-parse.** Both work; Knowledge uses the env var and the a4 hooks follow suit. Simpler and avoids a git subprocess per hook invocation. Claude Code sets this for every hook.
7. **Record file is kept on failure.** A Stop that emits violations keeps the record file so the next Stop re-validates the same set. Only a clean run deletes the record. This is how Knowledge does it; the effect is a retry cadence tied to actual stop cycles (Claude attempts a fix, stops, hook re-checks).
8. **Namespaced record directory `.claude/tmp/a4-edited/`.** Not `.claude/tmp/edited/` to avoid collision with Knowledge's hooks if both plugins run in the same project. Low-probability scenario but costs nothing to avoid.
9. **`disable-model-invocation: true` on `/a4:validate`.** Matches `/a4:drift` and `/a4:index`. These wrapper skills are deterministic utilities; the agent should not pick them up as a routing target. User must invoke explicitly.
10. **No separate ADR for the hook.** The hook is tooling that implements ADR-defined invariants (frontmatter schema, Obsidian conventions); it is not itself a design decision at ADR scope. Documented in README and this handoff. If a future change to the hook's blocking semantics or scope warrants an ADR, open a new one then.

## Thread closure

The prior handoff (`2026-04-24_1813`) listed this as the only remaining ADR open item:

> **Compass redesign** — still the only open item.

With Step 8 now `[x]`, the ADR's Next Steps list reads 13/13 complete. The `a4-redesign` thread has no known follow-up. Recommended posture for the next session:

- If the user starts a new topic, begin a fresh thread (new `topic:` slug, new subfolder under `plugins/a4/.handoff/`).
- If the user asks about a4 internals without a defined new topic, this thread's handoff chain (14 files in `plugins/a4/.handoff/a4-redesign/` plus this one = 15 files total) is the authoritative record. The ADR at `plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md` is the authoritative design summary.

### Known future-work candidates (NOT ADR items, NOT scheduled)

Surfaced in passing during this session but not chosen for implementation. Record here so they are visible but not pending:

- **Pre-commit hook or CI workflow using `/a4:validate`.** Entirely feasible — the validators exit 0/2 already support it. Would require a `.pre-commit-hooks.yaml` or `.github/workflows/a4-validate.yml`. Not opened because the current user's workflow is single-developer local.
- **Stop hook enhancement — workspace-wide sanity sweep on first Stop of a session.** Could complement the accumulator by doing one full-workspace validate on session start (or the first Stop) to surface pre-existing issues once, in a controlled place. Would need careful UX (the full-sweep output is potentially loud). Deferred indefinitely — user has `/a4:validate` for explicit invocation.
- **Extension of validators to accept `--files file1 file2 …`.** Would let the Stop hook invoke each validator exactly once per session (instead of once per edited file). Quality-of-life improvement; current loop is fast enough on normal workspace sizes.
- **`compass` Step 0.4: surface pending Stop-hook violations.** The record file, if it still exists at compass time, signals in-progress violations. Could be shown in the compass dashboard. Low priority.

These are not "still open" in any meaningful ADR sense — they are ideas, not commitments.

## Caveat — prior handoff's Compass claim was stale

The previous handoff (`2026-04-24_1813_topic-folder-layout.md`) asserted:

> `plugins/a4/skills/compass/SKILL.md` Step 1.2 (artifact scan) and Step 3 (gap diagnosis) still use the pre-ADR topic × stage grid. Rewrite for the per-item wiki+issue layout.

At the time that handoff was written (18:13), that claim was already false — commit `72f62ac24` at 16:16 the same day had rewritten compass for the wiki+issue layout. The prior handoff's author was working from stale information about compass state, even while correctly capturing everything else about the topic-folder-layout refactor.

The practical effect: this session's "Compass redesign" work reduced to (a) verifying compass was already aligned, (b) flipping the ADR checkbox, (c) making the validator-split decision, (d) building `/a4:validate` and the Stop hook. If the next session wonders why the ADR's Step 8 completion note covers both the earlier rewrite and this session's validator work, that is why — the bookkeeping was deferred and rolled in together.

No corrective action needed. The handoffs in the `a4-redesign/` chain are point-in-time records; the stale claim is preserved per DO NOT UPDATE policy.

## Files intentionally NOT modified

- **`plugins/a4/skills/compass/SKILL.md`** — already aligned in commit `72f62ac24`. Verified by reading; no further edit needed this session.
- **`plugins/a4/scripts/validate_frontmatter.py`, `validate_body.py`** — consumed as-is by both the new skill and the new hook. No change.
- **`plugins/a4/scripts/drift_detector.py`, `index_refresh.py`, `allocate_id.py`, `inject_includes.py`, `extract_section.py`, `read_frontmatter.py`** — unaffected.
- **`plugins/a4/skills/{drift,index,handoff,usecase,arch,plan,spark-brainstorm,spark-decide,auto-usecase,auto-bootstrap,web-design-mock}/`** — none interact with the validator invocation surface or the hook record file.
- **`.claude-plugin/plugin.json`** for a4 — per repo CLAUDE.md, plugin.json must NOT carry a version field. Version lives in `marketplace.json`. Correct as-is.
- **`plugins/a4/references/frontmatter-schema.md`, `obsidian-conventions.md`, `obsidian-dataview.md`** — the validator rules documented there are unchanged; only the invocation surface grew.
- **Prior handoffs in `plugins/a4/.handoff/a4-redesign/`** — 14 files preserved unchanged per DO NOT UPDATE policy, including the stale Compass claim in `2026-04-24_1813`.

## Working-tree state at handoff time

Two pre-handoff commits landed this session:

```
3a6ea40d2 feat(a4): add Stop-hook session validation for a4/ edits
4ca34820f feat(a4): add /a4:validate skill and close compass-redesign ADR item
```

Branch: `main`. After this handoff's own commit, main will be **22 commits ahead** of `origin/main` (19 before this session + 2 pre-handoff commits this session + 1 handoff-file commit).

Changes bundled into this handoff's own commit:

```
new file:   plugins/a4/.handoff/a4-redesign/2026-04-24_1859_validate-skill-and-stop-hook.md   # this file
```

## Explicitly rejected / not done this session

- **Wire validators into compass Step 3.** See design decision 1 — validator-split.
- **Use passive `additionalContext` in the Stop hook.** Replaced with `exit 2` blocking. Design decision 2.
- **Run validators workspace-wide in the Stop hook.** Scoped to session-edited files only. Design decisions 3 and 4.
- **Keep the Python transcript-parsing first draft.** Scrapped when the user pointed at Knowledge's pattern. The transcript approach was correct per-turn but missed multi-turn accumulation; the record-file approach handles both cleanly.
- **Re-edit compass SKILL.md.** Already aligned (commit `72f62ac24`); no changes needed.
- **Build a pre-commit hook or CI workflow.** Feasible follow-up; not implemented because the user runs single-developer local and `/a4:validate` + the Stop hook cover the interactive case.
- **Separate-commit the validate skill's ADR close from the marketplace bump.** Kept as one commit because they are one logical delivery.
- **Amend or rebase the two pre-handoff commits together.** They represent two distinct deliveries (skill vs hook) with their own rationales; clean git log is better than artificial compaction.

## Non-goals for next session

- Do not reopen the validator-split decision. `/a4:validate` is the skill surface; compass stays a navigation skill.
- Do not change the Stop hook to passive `additionalContext`. The `exit 2` blocking was chosen deliberately over `additionalContext`.
- Do not extend the Stop hook's scope beyond session-edited files. Workspace-wide is `/a4:validate`'s job.
- Do not re-introduce compass SKILL.md as a validator entry point.
- Do not mark any ADR Next Step as re-opened. The thread is closed.
- Do not bump `marketplace.json` for this handoff-file commit. Docs-only commits (adding a handoff snapshot) do not bump. The two skill + hook bumps already happened in `4ca34820f` and `3a6ea40d2`.
- Do not open a new ADR for the hook unless future changes to its blocking semantics or scope warrant it.

## Files to read first next session

If the next session resumes on a new topic, this block is probably not needed — read only what the new topic requires.

If the next session needs to understand what this thread landed:

1. **`plugins/a4/spec/2026-04-23-spec-as-wiki-and-issues.decide.md`** — the authoritative design summary. All 13 Next Steps `[x]`.
2. **`plugins/a4/README.md`** — the user-facing summary. Components, Hooks, Document Layout, Conventions, Wiki update protocol, Derived views, Workspace dashboard, Archive.
3. **`plugins/a4/skills/validate/SKILL.md`** + **`plugins/a4/hooks/`** — this session's deliverables.
4. **`plugins/a4/skills/compass/SKILL.md`** — if understanding the navigation surface matters.
5. This handoff + the 14 prior `a4-redesign/` handoffs as point-in-time records.
