---
timestamp: 2026-04-25_0301
topic: a4-hook-automation
previous: 2026-04-25_0244_consolidate-hooks-into-dispatcher.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-25_0301. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# Session focus

Short, narrowly-scoped follow-up to the prior session (`2026-04-25_0244_consolidate-hooks-into-dispatcher.md`): the consolidated dispatcher still shelled out to `uv run validate_*.py` / `uv run refresh_implemented_by.py` as subprocesses. This session replaced those nested subprocess calls with **in-process module imports**, eliminating the per-script `uv run` startup cost. That is the entire scope of the refactor. The thread topic `a4-hook-automation` is retained.

Shipped in a single commit: **`8e626b684`** (`refactor(a4): call sibling scripts via import, not uv run subprocess`). Plugin version bumped **1.13.1** (was 1.13.0). This is a patch bump — internal implementation change, no user-visible contract change on the hooks.

**The next session has been told to take on a larger, user-directed task: modularize `plugins/a4/scripts/` into a proper Python package.** Details in [§Next task — scripts modularization](#next-task--scripts-modularization) below. That section is written to stand alone: the next session should read it first.

# What got built (commit `8e626b684`)

## Modified: `plugins/a4/scripts/a4_hook.py` (~250 lines net delta: +123 / −140; file length roughly unchanged)

- **PEP-723 header**: `dependencies = []` → `dependencies = ["pyyaml>=6.0"]`. The dispatcher itself doesn't import yaml, but the sibling modules it now imports do, so uv must provision yaml into the dispatcher's venv.
- **New top-level `sys.path` prepend**: `Path(__file__).resolve().parent` is inserted at `sys.path[0]` unless already present. Makes sibling `.py` files importable as plain modules (`import validate_frontmatter as vfm`) regardless of how uv invokes Python. This is explicit rather than relying on Python's default script-dir auto-insertion.
- **Removed `_run_validator(...)` helper.** The old helper wrapped `subprocess.run(["uv", "run", str(script), str(a4_dir), file_path], ...)` and returned `(rc, combined_output)`. No longer needed.
- **`_report_status_consistency_post(...)`**: now `import validate_status_consistency as vsc`, resolves the file's relative path, calls `vsc.collect_file_mismatches(a4_dir, str(rel))` directly, and formats the mismatch list in-dispatcher (replicating the exact string shape `validate_status_consistency.py` prints in CLI mode, so `additionalContext` stays byte-for-byte compatible with the prior implementation).
- **`_report_status_consistency_session_start(...)`**: symmetric change — calls `vsc.collect_workspace_mismatches(a4_dir)`.
- **`_refresh_implemented_by(...)`**: now `import refresh_implemented_by as rib` and calls `rib.refresh_all(a4_dir, dry_run=False)` directly. Consumes the returned `Report` dataclass (`.changes: list[Change]`, `.errors: list[str]`). No JSON parse round-trip; the structured values flow in memory.
- **`_stop()`**: rewritten to import `validate_frontmatter as vfm` and `validate_body as vbody` once, pre-compute body-validator indices (`vbody.discover_wiki_pages/issues/sparks`) once, then loop the edited files calling `vfm.split_frontmatter` + (`vfm.check_missing_frontmatter` or `vfm.validate_file`) + `vbody.validate_file`. Aggregates `Violation` lists (one from each validator family) and re-renders the human-readable output in the same format the CLI used. Behavior preserved: rc=2 on any violation, rc=0 on clean, rc=0 on any library exception (with a short stderr note — unchanged non-blocking policy).
- **Error handling shape**. Every import site is wrapped in `try: import X except ImportError: ...`. Every library call is wrapped in `try: ... except Exception: ...` so a bug in a sibling module cannot strand the user. For non-Stop events the failure is silent (return 0 with no output); for Stop, a one-line stderr note + return 0. This matches `hook-conventions.md` §5 verbatim — only the failure *source* changed (library exception vs. subprocess non-zero).
- **Fast path pattern preserved**. Top-level imports still only pull `sys` and `pathlib.Path` (the latter needed for the `sys.path` setup). Each subcommand imports its dependencies locally, so the post-edit hot path still pays no yaml import cost if it hits any of the early-exit guards (empty stdin, non-a4 path, etc.).

## Modified: `plugins/a4/references/hook-conventions.md`

Added a new subsection to §3 (Language and invocation), titled **"In-process module imports for sibling scripts"**, documenting:
- Sibling scripts called via `import`, not nested `uv run`.
- Single-`uv run` per hook event, not per script call.
- Dispatcher is the deps aggregator (pyyaml declared on `a4_hook.py`, not re-declared everywhere).
- Standalone CLI use of the sibling scripts still supported — each keeps its own PEP-723 header for that path.

## Modified: `.claude-plugin/marketplace.json`

Plugin `a4` bumped **1.13.0 → 1.13.1**. No other plugin entries touched.

# Why in-process imports over subprocess

The subprocess layer was load-bearing in the prior design only because each validator script was historically launched standalone via `uv run`. With the consolidated dispatcher (prior session), the dispatcher was already paying one `uv run` startup cost for its own invocation — then paying *another* `uv run` startup for each script it shelled out to. That second layer bought nothing:

- **Dispatcher and validators run in the same trust boundary.** Subprocess isolation had no safety benefit here.
- **Structured-value round-trip via JSON.** Several helpers (`_refresh_implemented_by`) were already re-parsing the subprocess's `--json` stdout just to get back a dataclass that existed in Python moments earlier. In-process import hands the dataclass over directly.
- **Every `uv run` pays interpreter + venv-activation startup** (~100–300ms observed on this host). The old Stop hook paid this 2N times for N edited files; the new Stop pays it once total.
- **Error propagation improved, not degraded.** Subprocess error paths required guessing at rc semantics (0=OK, 2=violations, anything-else=internal-error). In-process, library exceptions are `try/except Exception` — more direct, same non-blocking behavior.

The only mild trade-off is that the dispatcher's PEP-723 header now lists pyyaml even though `a4_hook.py` itself never imports it. Accepted as the explicit cost of the dispatcher being the sole `uv run` entry point.

# Verification performed (this session)

Directly in this session (not on a real `a4/` workspace):

- **Syntax** — `python3 -m py_compile scripts/a4_hook.py` passes.
- **JSON validity** — `hooks.json` and `marketplace.json` both parse.
- **Silent-skip paths** — all rc=0 with no stdout:
  - post-edit: empty stdin, malformed JSON, non-`a4/` file path
  - stop: empty stdin
  - session-start: no env vars (via `env -i`)
- **End-to-end on fixture** at `/tmp/a4-dispatcher-import-test/` (now deleted):
  - `a4/usecase/1-login.md` + `a4/task/10-auth.md` + `a4/idea/20-bad.md` (status=promoted, promoted:[]) + `a4/usecase/2-broken.md` (frontmatter-only, invalid).
  - **post-edit** on `idea/20-bad.md` → emitted `additionalContext` JSON with the correct mismatch (`empty-promoted-list-idea`). rc=0.
  - **post-edit** on the two UCs → silent, rc=0 (no mismatches in connected component; broken UC yields no report but doesn't crash).
  - **Record file** (`.claude/tmp/a4-edited/a4-edited-smoke-imp.txt`) contained all three edited paths.
  - **stop** → rc=2. Stderr reported `missing-frontmatter` violation on `usecase/2-broken.md` with the exact same wording `validate_frontmatter.py` CLI would print.
  - **session-start** → rc=0. Refreshed `implemented_by` on `usecase/1-login.md` from `['task/10-old-ref']` to `['task/10-auth']` (actually wrote to disk). Reported 1 error (broken UC) and 1 idea status-consistency mismatch. Emitted both `additionalContext` and `systemMessage` in the merged payload.
  - **Post-refresh file content** confirmed — UC file on disk now carries `implemented_by: [task/10-auth]`.
- **uv cache check** — after the first run (which installed pyyaml once into the dispatcher's venv), subsequent runs showed no "Installed N package(s)" line, so the venv is cached.

# Not verified

- **Real `a4/` workspace end-to-end.** No live workspace in this marketplace repo. Same caveat as every prior a4-hook-automation handoff.
- **Subjective edit-responsiveness on PostToolUse.** Each Write/Edit/MultiEdit now pays exactly one `uv run` startup (down from two); not measured against human perception.
- **Stop budget under edit-heavy sessions.** The biggest win should be here — validators now pay one shared `uv run` startup instead of 2N. Not stress-tested.
- **pyyaml version floor.** Declared `pyyaml>=6.0`. Sibling scripts declare the same. No older-version testing performed.
- **`sys.path` insertion on edge invocations** (e.g., `uv run - < a4_hook.py`, `python -m`). The explicit insert should cover those; not tested.

# Next task — scripts modularization

**User directive for the next session: modularize `plugins/a4/scripts/` — the folder of standalone Python scripts — into a proper Python package.**

This is the explicit instruction passed via `/handoff` args: "다음 작업을 @plugins/a4/scripts/ 폴더내 python script 모듈화." The in-process-import refactor shipped this session is the **minimum** integration — the `sys.path` hack and the per-script PEP-723 headers are symptomatic of the folder not being a real package. Everything below is scope for the next session, not this one.

## Current inventory

`plugins/a4/scripts/` contents (at session end):

| File | Role | Used by |
|------|------|---------|
| `a4_hook.py` | Hook dispatcher (this refactor's subject) | `hooks/hooks.json` |
| `validate_frontmatter.py` | Frontmatter schema validator | `a4_hook.py` (stop), `/a4:validate`, standalone CLI |
| `validate_body.py` | Body-level Obsidian-convention validator | `a4_hook.py` (stop), `/a4:validate`, standalone CLI |
| `validate_status_consistency.py` | Cross-file status-consistency validator | `a4_hook.py` (post-edit, session-start), `/a4:validate`, standalone CLI |
| `refresh_implemented_by.py` | Maintains UC `implemented_by:` reverse-links | `a4_hook.py` (session-start), `/a4:plan` Phase 1, standalone CLI |
| `transition_status.py` | Single-writer for status transitions / cascades | Various skills; not touched by this refactor |
| `allocate_id.py` | Allocates next-available numeric id per issue family | Issue-creation skills |
| `drift_detector.py` | Cross-session wiki-page / marker / orphan checks | `/a4:validate` and related |
| `extract_section.py` | Extracts a markdown section by heading | Skills that need precise section slicing |
| `inject_includes.py` | Include-directive expansion | Doc-generation paths |
| `read_frontmatter.py` | Tiny `yaml.safe_load` wrapper around a file's frontmatter | Skills |
| `index_refresh.py` | Rebuilds workspace index(es) | Maintenance commands |

All twelve are standalone PEP-723 scripts. Each has its own `dependencies = [...]` header and its own `main()` guarded by `if __name__ == "__main__":`. Their CLI contracts are consumed by many skills and commands — the migration cannot break those.

## Observed duplication (drivers for the refactor)

Grepping across the folder (from memory of this session's reading + prior sessions):

- **`split_frontmatter`** exists in at least four files with *different return signatures*:
  - `validate_frontmatter.py` → `(fm: dict|None, body: str)`
  - `validate_body.py` → `(fm: dict|None, body: str, body_start: int)`
  - `validate_status_consistency.py` → `fm: dict|None` (one value)
  - `refresh_implemented_by.py` → `(fm: dict|None, raw_fm: str, body: str)`
  - Four incompatible signatures that all do the same YAML-fence parsing.
- **`_normalize_ref` / `normalize_ref`** — identical behavior in `validate_status_consistency.py` and `refresh_implemented_by.py`.
- **`_is_empty`, `_is_int`, `_is_non_empty_list`** — scattered across validators.
- **`WIKI_KINDS`, `ISSUE_FOLDERS`** constants — duplicated between `validate_frontmatter.py` and `validate_body.py` (and likely elsewhere).
- **`discover_files` / `discover_wiki_pages` / `discover_issues` / `discover_sparks`** — related workspace-traversal logic in different files.
- **`collect_family`** (decision/usecase/idea/task iteration) — candidate for shared use.
- **`Violation` / `Mismatch` / `Change` dataclasses** — each script defines its own; some have overlapping shape.

The `a4_hook.py` dispatcher is the first consumer to actually need many of these at once, which is how the duplication became visible.

## Proposed directions (decide in next session)

Three plausible designs. Not ranked — the next session should weigh the trade-offs against the user's preferences before committing.

### Option A — Minimal package (`a4_scripts/`)

- Rename the directory to `a4_scripts/` (or create a package alongside the flat scripts).
- Add `__init__.py`; move each existing `.py` under it as a submodule.
- Extract a shared `a4_scripts/common.py` for `split_frontmatter`, `normalize_ref`, `WIKI_KINDS`, `ISSUE_FOLDERS`, discovery helpers.
- Dispatcher becomes `from a4_scripts import validate_frontmatter, validate_body, ...` — drop the `sys.path` hack.
- **Backward compat concern**: every skill/command currently shelling out to `uv run plugins/a4/scripts/<name>.py` breaks. Mitigation: keep the old file paths as thin shims that `import` from the package and call `main()`, or update all callers (there are many — grep needed).

### Option B — Package + entry points via `uv run python -m`

- Same package structure as A, plus expose CLI entry points via `python -m a4_scripts.<module>`.
- Consolidate the per-file PEP-723 headers into one `pyproject.toml` (or one script-mode header on a single thin launcher). Under uv, this is `uv run --project plugins/a4 python -m a4_scripts.validate_frontmatter <args>`.
- Cleaner, but every caller call site must change from `uv run scripts/<name>.py` to `uv run --project <plugin-root> python -m a4_scripts.<name>`. Wider blast radius than A.

### Option C — Keep flat files, extract shared helpers only

- Don't turn the folder into a package. Just add `plugins/a4/scripts/_common.py` (or similar) and have each existing script import from it (`from _common import split_frontmatter, ...`). Requires the same `sys.path` insertion the dispatcher now does.
- Lowest disruption, smallest payoff. De-duplicates the helpers but leaves every script with its own PEP-723 header and doesn't clean up the import hack in the dispatcher.
- Arguably the right minimum if the user is risk-averse about breaking skill callers.

The in-process-import work shipped this session is compatible with all three directions. Nothing this session did has to be reverted.

## Suggested migration ordering (if Option A is chosen)

1. **Survey callers.** `grep -R 'scripts/[a-z_]\+\.py' plugins/a4/ global/ .claude/` (and repo-wide) to enumerate every `uv run scripts/<name>.py` invocation. Classify into: (a) hook invocations (already go through `a4_hook.py`, no change), (b) skill invocations (SKILL.md or inline shell), (c) slash-command commands (`commands/*.md`), (d) docs/references with example snippets.
2. **Create `a4_scripts/` package with `__init__.py` + `common.py`.** Move the four scripts already imported by the dispatcher (`validate_frontmatter`, `validate_body`, `validate_status_consistency`, `refresh_implemented_by`) first — their only non-skill caller is the dispatcher, so the blast radius is small.
3. **Update the dispatcher** to `from a4_scripts import ...`; drop the `sys.path` insert and the `pyyaml>=6.0` dependency-header entry (pyyaml moves to the package-level spec). Re-run this session's verification fixture.
4. **Extract common helpers** into `a4_scripts/common.py`, one at a time, with per-commit regression checks. Canonical `split_frontmatter` first.
5. **Migrate the remaining eight scripts** (`transition_status`, `allocate_id`, `drift_detector`, `extract_section`, `inject_includes`, `read_frontmatter`, `index_refresh`, plus `a4_hook` itself if the package layout admits a hook submodule). At this stage, external skill callers still use the old paths — keep shims if needed.
6. **Decommission the old paths** once callers are migrated. Either delete the flat files or leave them as one-line shims that `import` from the package and call `main()` for a release or two, then remove.
7. **Tests.** The prior handoff's follow-up #7 ("test harness for the dispatcher") lands naturally here — a package admits a `tests/` sibling directory with pytest fixtures. With the hook logic imported in-process, tests can exercise the dispatcher via direct calls rather than subprocess; much faster and more precise.

## Risks specifically for the next session

- **Many skill/command callers invoke these scripts by path.** Bulk-updating markdown files that contain shell snippets is doable but needs a careful grep-audit. Missing one breaks that skill silently at runtime.
- **PEP-723 header consolidation**. Currently every script is self-contained; a user running `uv run validate_frontmatter.py` from their own terminal gets deps auto-installed. If we delete the per-file headers, that ergonomic goes away unless we replace it with a project-level spec. Consider keeping thin shim files with PEP-723 headers that `python -m a4_scripts.<name>` under the hood.
- **Nothing in `a4/` workspace assumes anything about script organization.** That's not a migration risk — but skills that read scripts' source as string (unlikely but possible) would break.
- **`a4_hook.py` PEP-723 header** currently names `pyyaml>=6.0`. Once the sibling scripts are a package and the package declares its deps centrally, that line should move. Don't forget to remove it from the dispatcher header as part of the refactor.

# Follow-ups (carried forward)

Re-evaluated against this session's work. Numbering preserves the prior handoff's scheme where applicable.

1. **`transition_status.py --sweep` SessionStart hook.** Still deferred. After this session's refactor, the integration path is extra clean: once `transition_status.py` is importable as a module, the dispatcher's `_session_start()` can call its sweep function directly, following the write-phase ordering rule (refresh first, sweep second, then read-phase report).
2. **`compass` wrapper.** Still open.
3. **SessionStart `systemMessage` for status-consistency-only output.** Still open; unchanged by this session.
4. **Observe the dispatcher in a real workspace.** Same priority list as before: (a) verify merged SessionStart payload rendering, (b) measure post-edit startup overhead subjectively (now one `uv run` instead of two — should be noticeably better), (c) stress-test Stop budget.
5. **`refresh_implemented_by.py` module docstring.** Still open (one-line cleanup).
6. **Hard-fail surfacing design.** Still open. The non-blocking policy (§5) still swallows every `Exception` in the non-Stop subcommands. With in-process imports, exceptions are closer (not filtered through subprocess rc translation), so the surfacing refinement (terse stderr note on uncaught exceptions) is easier to land cleanly.
7. **Test harness for the dispatcher.** Unblocked by this session. In-process imports make pytest-driven testing a direct path: import `a4_hook` module, call `_post_edit()` with a patched stdin / env, assert on stdout. No subprocess fixturing required. Lands naturally with the scripts-modularization task above.
8. **Stop budget elasticity.** Reduced in urgency by this session. The per-file `uv run` overhead is gone; remaining cost is pure Python validator work. If this ever becomes a problem, the remaining lever is parallelizing the per-file loop via `concurrent.futures` inside `_stop()`.

# Explicitly untouched

- **`plugins/a4/hooks/hooks.json`** — unchanged. Invocation line for `a4_hook.py` still `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/a4_hook.py <subcommand>`.
- **`plugins/a4/hooks/README.md`** — unchanged.
- **`plugins/a4/hooks/cleanup-edited-a4.sh`, `hooks/sweep-old-edited-a4.sh`** — retained bash hooks; untouched.
- **Sibling validator scripts** (`validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`, `refresh_implemented_by.py`). Their public function signatures are the dispatcher's contract now — they were imported, not modified. CLI paths still work (each keeps its PEP-723 header).
- **Other scripts** (`allocate_id.py`, `drift_detector.py`, `extract_section.py`, `inject_includes.py`, `read_frontmatter.py`, `index_refresh.py`, `transition_status.py`). Touched only by the next session's modularization task.
- **All skills and commands.** None modified.
- **All other plugins in the marketplace.** Only `a4` edited.
- **Prior-thread handoffs.** Still immutable snapshots.

# Key files to re-read on the next session

- **`plugins/a4/scripts/a4_hook.py`** — the new import pattern. The `sys.path` insertion at the top and the local `import X as Y` inside each `_report_*` / `_refresh_*` / `_stop` function is where the modularization task will start rewriting.
- **`plugins/a4/scripts/validate_frontmatter.py`, `validate_body.py`, `validate_status_consistency.py`, `refresh_implemented_by.py`** — the four scripts whose public helpers are now the dispatcher's import surface. Before turning them into a package, note which of their top-level functions the dispatcher depends on (`split_frontmatter`, `validate_file`, `check_missing_frontmatter`, `discover_wiki_pages`, `discover_issues`, `discover_sparks`, `collect_file_mismatches`, `collect_workspace_mismatches`, `refresh_all`, and the `Violation`/`Mismatch`/`Report`/`Change` dataclasses). Those are the stable API; everything else inside each file can be restructured freely.
- **`plugins/a4/scripts/transition_status.py`** and the other seven unrelated scripts — the next session needs to audit all of them before picking a package layout.
- **`plugins/a4/references/hook-conventions.md`** — §3 now describes the in-process-import pattern. Update this section again when the modularization lands (the `sys.path` note becomes stale; the pyyaml aggregation note may move to a package-spec note).
- **`plugins/a4/hooks/hooks.json`** — verify no changes needed by the modularization (the entrypoint string `scripts/a4_hook.py` is stable unless the dispatcher itself moves).
- **Prior handoff `2026-04-25_0244_consolidate-hooks-into-dispatcher.md`** — the six-principle hook-conventions summary and the rejected-alternatives list remain relevant. The "N-entry per event" and "mixed-language dispatcher" rejections explain why `a4_hook.py` exists as a single Python entry point in the first place.

# Outstanding parked threads

- **`a4-hook-automation`** (this thread) — open. Live follow-ups listed above; chief next-session task is the scripts-modularization work.
- **`uc-status-transition-system`** — formally concluded; two minor parked items remain (tighter `## Section` substring checks; body-section drift validator for `final` decisions). Neither commissioned.
- **`idea.promoted` / `brainstorm.promoted` materialization** — still open from the status-transition thread's follow-up #5. Unrelated to this thread.
- **`a4-redesign`, `experiments-slot`, `idea-slot`, `decision-slot-unification`** — unaffected by this session.
