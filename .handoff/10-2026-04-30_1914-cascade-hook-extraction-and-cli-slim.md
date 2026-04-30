---
sequence: 10
timestamp: 2026-04-30_1914
timezone: KST +0900
topic: a4-status-cascade-hook
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1914. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Move the a4 status-transition writer from an explicitly-invoked CLI (`scripts/transition_status.py --file ... --to ...`) to a PostToolUse hook so the LLM can edit `status:` directly and the hook materializes cascades (supersedes / discarded / revising) on related files. Keep a CLI sweep path for recovery from edits that bypassed the hook.

## Current State

- Branch: `main`, ahead of `origin/main` by 82 commits (no push performed).
- HEAD: `d436178ae` — `refactor(a4): move status-change cascade from CLI writer to PostToolUse hook (v13.0.0)`. Working tree clean.
- Steps 1–3 of the four-step migration plan landed in HEAD:
  1. Cascade primitives extracted to a new shared module.
  2. `pre-edit` / `post-edit` cascade flow added to the dispatcher; `hooks.json` + bash housekeeping updated.
  3. `transition_status.py` slimmed to sweep-only.
- Step 4 (skill / reference / agent doc churn — ~50 files still cite the old writer flow) is **not** done. This is the main outstanding work.

## Changes Made

All in HEAD (`git show d436178ae`):

- **New `plugins/a4/scripts/status_cascade.py`** — non-runnable shared module (no PEP-723) holding cascade primitives:
  - Result types: `Change`, `Report`, `SkipDecision`.
  - Frontmatter IO: `parse_fm`, `rewrite_frontmatter_scalar`, `write_file`.
  - Discovery: `find_tasks_implementing`, `find_reviews_targeting`.
  - Engines: `apply_status_change`, `apply_reverse_cascade`, `apply_supersedes_chain`.
  - Dispatcher: `run_cascade`.
- **`plugins/a4/scripts/transition_status.py`** slimmed 798 → ~165 lines. CLI is now sweep-only:
  ```
  uv run transition_status.py <a4-dir> [--dry-run] [--json]
  ```
  Removed: `--file/--to/--validate/--reason/--sweep` flags, `transition()` function, `detect_family`, `_resolve_rel`, validate path. The filename is preserved (≈125 external doc references) — to be retired or renamed when step 4's doc churn lands.
- **`plugins/a4/scripts/a4_hook.py`** — two additions:
  - New `pre-edit` subcommand: PreToolUse on `Write|Edit|MultiEdit`. Snapshots on-disk `status:` of the file about to be edited into `.claude/tmp/a4-edited/a4-prestatus-<sid>.json` (a `{abs_path: pre_status}` map).
  - Extended `_post_edit`: after recording, calls `_run_status_change_cascade` which (a) reads stashed pre, (b) reads current post, (c) drops the stash entry, (d) if status changed and transition is legal per `FAMILY_TRANSITIONS`, runs `run_cascade` and refreshes `updated:` on the primary via `apply_status_change`, (e) emits both `additionalContext` and `systemMessage` per `docs/hook-conventions.md` §6. Order: record → cascade → consistency report (so the consistency report sees the post-cascade state).
- **`plugins/a4/hooks/hooks.json`** — added PreToolUse entry; updated PostToolUse description; rewrote top-level description to reflect new flow.
- **`plugins/a4/hooks/cleanup-edited-a4.sh` + `sweep-old-edited-a4.sh`** — extended to also clean / sweep `a4-prestatus-<sid>.json`.
- **`.claude-plugin/marketplace.json`** — a4 12.2.0 → 13.0.0 (breaking CLI change).

## Key Files

- `plugins/a4/scripts/status_cascade.py` — shared cascade engine. Edit here for cascade-rule changes; both writer CLI (sweep) and the hook depend on it.
- `plugins/a4/scripts/a4_hook.py` — hook dispatcher. `_pre_edit` (lines around 70–180), `_run_status_change_cascade` + `_emit_cascade_context` (the new chunk after `_post_edit`).
- `plugins/a4/scripts/transition_status.py` — recovery sweep CLI only.
- `plugins/a4/hooks/hooks.json` — wiring; PreToolUse fires on `Write|Edit|MultiEdit`.
- `plugins/a4/docs/hook-conventions.md` — design contract followed by the new hook (state classification §1–2, output channels §6). **Mention of `a4-prestatus-*.json` not yet added there**; consider a small follow-up to update the example tables.
- `plugins/a4/CLAUDE.md` — project instructions for editing this plugin (frontmatter contracts, etc.).

## Related Links

None — no GitHub issues / PRs / wiki pages were referenced in this session. The work is local to this monorepo.

## Decisions and Rationale

- **Pre/post on-disk snapshot, not git diff.** Initial sketch was to reuse the Stop hook's HEAD-vs-working-tree pattern. User suggested capturing pre/post directly via PreToolUse + PostToolUse for precision; accepted because HEAD-vs-working-tree shows cumulative deltas across multiple session edits, while a pre/post pair is exactly per-edit.
- **`updated:` is refreshed by the hook.** Mirrors the old writer's atomic `status:`+`updated:` write. The "post-hoc rewrite confuses the LLM" concern was discussed and dismissed: the same concern applies equally to the old writer (which also rewrote files outside the LLM's edit), and emitting cascade results as `additionalContext` keeps the LLM informed. See "Important Dialog" below.
- **Dry-run / preview moves to `search.py`.** User pointed out reverse-link cascade preview is exactly what `search.py --references X --references-via implements` does. Forward supersedes-chain preview is a single frontmatter read. So `transition_status.py --dry-run` lost its reason to exist on the writer path.
- **Illegal direct edits stay the Stop hook's problem.** The cascade hook explicitly skips when `is_transition_legal(family, pre, post)` is false — Stop hook's `markdown_validator.transitions` (HEAD-vs-working-tree) catches them and returns rc=2. This avoids cascading off a half-bad transition.
- **Filename `transition_status.py` preserved.** Renaming to e.g. `sweep_supersedes.py` was tempting (the script's job has narrowed) but would force ~125 doc references to update in the same commit. Deferred to step 4 doc churn.
- **Version bump 12.2.0 → 13.0.0.** Removing `--file/--to/--validate/--reason/--sweep` is a breaking CLI surface change.

## Important Dialog

User shaped the design with several sharp pushes:

- "transition_status.py로 updated: 갱신해도 다음 read에서 혼란 발생은 동일할꺼 같은데?" — pointed out the "post-hoc rewrite" concern wasn't a unique cost of the hook approach. Accepted; `updated:` refresh stays in the hook.
- "cascade 결과가 이런난다고 context로 알려주면 되잖아." — settled the cascade-visibility concern by emitting both `additionalContext` and `systemMessage`.
- "그건 transition_status말고 plugins/a4/scripts/search.py로 가능해 보이는데." — collapsed the dry-run / preview rationale; `search.py` already covers reverse-link cases.
- "pre, post로 변경전과 후를 알면 정확하게 판단 가능할듯." — chose the PreToolUse + PostToolUse snapshot pattern over git diff.

User worked in `auto` mode with explicit `진행` confirmations after each step.

## Validation

Run from `plugins/a4/scripts/`:

| Check | Command | Result |
|-------|---------|--------|
| Syntax | `python3 -c "import ast; ast.parse(open('status_cascade.py').read()); ast.parse(open('transition_status.py').read()); ast.parse(open('a4_hook.py').read())"` | OK |
| Imports | `uv run --with pyyaml python -c "import status_cascade, transition_status, a4_hook"` | OK |
| Sweep CLI help | `uv run transition_status.py --help` | OK (sweep-only surface) |
| End-to-end smoke (legal transition) | Custom fixture under `/tmp/a4hook-smoke/` (now removed). Script: `pre-edit` snapshot of `usecase/3-foo.md @ implementing` → simulated edit to `revising` → `post-edit` produced cascade flip on `task/4-foo-impl.md` (`progress → pending`), refreshed both `updated:` to today, emitted `additionalContext` + `systemMessage`, dropped stash entry. | Pass |
| End-to-end smoke (cosmetic edit) | Same fixture, edit-only-`title:`, status unchanged. | Silent no-op, stash dropped. Pass |
| End-to-end smoke (illegal transition) | `revising → shipped` (skips `implementing`). | Cascade did not fire; task status preserved. Pass |

Not run: full `validate.py` workspace sweep against a real `a4/` project — there is no real workspace fixture in this repo. The local `A4/` directory has a different structure (`issues.yml`) and is not an a4 workspace. Run `/a4:validate` against a real a4 project to gain confidence before relying on the new hook in production.

Smoke fixture has been cleaned up (`rm -rf /tmp/a4hook-smoke`).

## Known Issues and Risks

- **Doc churn outstanding.** ~50 files (skills, references, agents, README, hook-conventions.md) still describe the old "use `transition_status.py` to flip status" flow. See list under `git grep -l transition_status plugins/a4`. Until updated, skills/agents will hand the LLM stale guidance.
- **`hook-conventions.md` not yet updated** to mention the new `a4-prestatus-<sid>.json` session file or the cascade hook's output channels (it still cites `refresh-implemented-by` retired in v6.0.0 as the only "both channels" example).
- **No real-workspace integration test.** Smoke tests used a tmp fixture; behavior on a populated a4 workspace with multi-step edits, MultiEdit calls, or files newly created (no pre-status snapshot) is by-design but unverified end-to-end.
- **Stop hook's transition-legality safety net unchanged.** It still uses HEAD-vs-working-tree git diff. If the user does a legal status edit + cascade, then later does another legal edit before committing, the safety net's "current vs HEAD" delta may differ from any single pre/post pair the cascade hook saw. This was already true before this refactor; flagged because it's adjacent surface.
- **`transition_status.py` filename now misleading.** Its job is supersedes-chain recovery, not transition writing. Deferred rename to step 4.

## Next Steps

1. **Step 4 — doc churn.** Sweep skills / references / agents / README / hook-conventions.md for "use transition_status.py to flip status" / "scripts/transition_status.py" guidance and replace with:
   - "Edit `status:` directly; PostToolUse hook handles cascades + `updated:`."
   - "Preview cascade impact via `search.py --references <ref> --references-via implements` (or `--folder review --target <ref>`) before flipping."
   - "Use `transition_status.py <a4-dir>` for supersedes-chain recovery only."
   Start point: `git grep -l transition_status plugins/a4` (50 files).
2. Update `plugins/a4/docs/hook-conventions.md` §1 (state classification) example to add `a4-prestatus-<sid>.json` and §6 (output channels) to cite the cascade hook as the live "both channels together" example.
3. Consider renaming `scripts/transition_status.py` → `scripts/sweep_supersedes.py` (or similar) once step 4 is done. Touch all references in one diff.
4. Run a `/a4:validate` sweep on a real a4 workspace after step 4 to confirm no docs reference removed CLI flags.
5. Optional: add a unit test under `plugins/a4/scripts/` (none exist today) covering the pre/post hook flow with a fixture.

## Open Questions

- Should the cascade hook also emit when `cascades` is empty but `updated:` was refreshed (i.e., a status-changed primary with no related files)? Currently silent — the LLM only sees feedback when other files were touched. Probably fine, but worth confirming once skills are updated.
- After step 4, is there value keeping `transition_status.py` at all, or should sweep recovery move into a `/a4:validate --fix` subcommand? User has not weighed in.
- `markdown_validator.transitions` (Stop hook's safety net) reads HEAD vs working tree — should it instead read the pre/post stash for tighter scoping? Out of scope here, but adjacent.

## Useful Commands and Outputs

```bash
# Inspect the migration commit
git show d436178a

# Step-4 starting point: every file still naming the old writer
git grep -l transition_status plugins/a4

# Slimmed CLI shape
uv run plugins/a4/scripts/transition_status.py --help

# Recovery sweep (read-only preview)
uv run plugins/a4/scripts/transition_status.py <a4-dir> --dry-run --json

# Verify shared module imports cleanly
( cd plugins/a4/scripts && uv run --with pyyaml python -c "import status_cascade, transition_status, a4_hook; print('ok')" )

# Hook smoke pattern (mirrors what was tested manually):
#   1. Build a fixture under /tmp with a4/usecase/<id>.md + a4/task/<id>.md
#   2. echo '{"tool_name":"Edit","session_id":"sid","tool_input":{"file_path":"<abs>"}}' \
#        | CLAUDE_PROJECT_DIR=<proj> uv run plugins/a4/scripts/a4_hook.py pre-edit
#   3. Mutate the file's status: scalar
#   4. Pipe the same payload to `a4_hook.py post-edit` and read additionalContext + cascade flips
```
