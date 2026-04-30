---
sequence: 6
timestamp: 2026-04-30_1538
timezone: KST +0900
topic: a4-validator-hardening
previous: 5-2026-04-30_1303-cascade-trigger-map-and-engine-consolidation.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1538. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Continue Next Steps #1-#3 from handoff 5, in priority order:

1. Sharpen `--dry-run` semantics in `transition_status._apply_status_change` so dry-run becomes a true preview (parse + rewrite, skip only the disk write).
2. Lift `collect_family` / `read_fm` to shared layers and route cascade target discovery through `RefIndex` — closes the `#<id>` shorthand correctness gap. Split into two commits: shared-helpers refactor first, then `RefIndex` resolution.
3. Land the static `task.files:` artifact-path enforcement that handoff 5 listed as deferred item #4 in `frontmatter-schema.md`.

This thread continues directly from handoff 5 (`a4-validator-hardening`). Starting state: `transition_status.py` engine consolidation (`d3f1142e7`) plus the handoff-5 docs commit (`f5c13b5ed`). This session adds four substantive commits and bumps the a4 marketplace from `9.6.1` to `9.7.0`.

## Current State

- Branch: `main`. Working tree clean.
- HEAD: `222ace36e feat(a4): enforce task.files: artifact-path contract`.
- a4 marketplace version: `9.7.0` (`.claude-plugin/marketplace.json`).
- All three registered checks present: `frontmatter`, `status`, `transitions`. Verified via `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`.
- Module sizes (current): `transition_status.py` 843 lines, `frontmatter.py` 580, `status_consistency.py` 461, `common.py` 128, `markdown.py` 250.
- Cascade target discovery now resolves through `RefIndex`, so `#<id>` / `<family>/<id>` / `<id>-<slug>` / `<family>/<id>-<slug>` all reach the same file.
- Static frontmatter rule `task-files-bad-artifact-path` enforces the artifact-only contract on `task.files:`.

## Changes Made

This session's commits since handoff 5 (`f5c13b5ed`), oldest first. Use `git show <sha>` for exact file-by-file changes.

- `771068c7f fix(a4): make transition_status --dry-run a true preview` — moves `if dry_run: return` in `_apply_status_change` from before `_parse` to right before `write_file`. Dry-run now runs the full `_parse` + `rewrite_frontmatter_scalar` pipeline and only skips the actual disk write, so any parse / rewrite failure a real run would hit surfaces in the preview. Docstring updated to describe the new dry-run contract. Marketplace 9.6.1 → 9.6.2. Resolves handoff 5 Next Step #1.

- `5594e4bb4 refactor(a4): lift collect_family / read_fm into shared layers` — promotes three duplicate primitives:
  - `markdown.read_fm(path) -> dict | None` — convenience wrapper around `extract_preamble(path).fm`. Replaces the private `_fm` shim in `markdown_validator.status_consistency`.
  - `common.iter_family(a4_dir, family) -> list[(Path, dict)]` — single-source the "iter_issue_files + parse + skip None" walk pattern.
  - `common.collect_family(a4_dir, family) -> dict[str, dict]` — promoted verbatim from `status_consistency`; built on `iter_family`. `collect_specs(...)` stays in `status_consistency` as a back-compat alias.

  Rewrites `transition_status.find_tasks_implementing` / `find_reviews_targeting` / `find_usecases_superseded_by` and `sweep()` against `iter_family`; `transition_status.py` no longer imports `iter_issue_files`. No behavior change — same files visited in same order, same skip semantics for malformed frontmatter, same cascade fan-out and report shape. Marketplace 9.6.2 → 9.6.3. Resolves the first half of handoff 5 Next Step #2.

- `be65ba90f fix(a4): resolve cascade target refs through RefIndex` — `transition()` and `sweep()` build a `RefIndex(a4_dir)` once and thread it through `_run_cascade` into the engines and `find_*` helpers. Each `implements:` / `target:` / `supersedes:` entry is resolved via `index.canonical` / `index.resolve`, so all four accepted ref forms (`#<id>`, `<family>/<id>`, `<family>/<id>-<slug>`, `<id>-<slug>`) reach the same file. The supersedes-chain keeps a path-form fallback for entries the index cannot resolve (cross-family-by-prefix skips, missing-file errors). Also deletes `find_usecases_superseded_by` — declared but never called by any cascade or sweep path. Marketplace 9.6.3 → 9.6.4. Resolves the second half of handoff 5 Next Step #2.

- `222ace36e feat(a4): enforce task.files: artifact-path contract` — adds static rule `task-files-bad-artifact-path` to `markdown_validator.frontmatter` (in `_validate_task_files`). Every entry in a task's `files:` list must start with `artifacts/task/<kind>/<id>-<slug>/`; for `kind: spike` only, `artifacts/task/spike/archive/<id>-<slug>/` is also accepted. Skip-when semantics: malformed `kind`, missing `id`, or filename id-slug mismatch all defer to other rules (`id-filename-mismatch`, `kind-required`, etc.) rather than emitting a redundant violation. Updates `references/frontmatter-schema.md` to drop the `task.files:` enforcement entry from "Known deferred items"; the `research` `complete` *existence* preflight remains deferred and slides up to item #4. Marketplace 9.6.4 → 9.7.0. Resolves handoff 5 Next Step #3.

## Key Files

- `plugins/a4/scripts/transition_status.py` (843 lines):
  - `_apply_status_change` — dry-run gate now sits right before `write_file`; full parse + rewrite happens for both real and preview modes.
  - `find_tasks_implementing(a4_dir, uc_canonical, index)` and `find_reviews_targeting(a4_dir, canonical, index)` — RefIndex-resolved comparisons.
  - `_apply_supersedes_chain(a4_dir, family, rel_path, today, dry_run, report, index)` — RefIndex resolution with path-form fallback for cross-family-by-prefix skips and missing-file errors.
  - `_run_cascade(... index)` — threads `RefIndex` from `transition()` / `sweep()` to the engines.
  - `find_usecases_superseded_by` removed (was dead code).
- `plugins/a4/scripts/common.py` (128 lines): now home for `iter_family` and `collect_family`. Imports `read_fm` from `markdown`.
- `plugins/a4/scripts/markdown.py` (250 lines): `read_fm(path) -> dict | None` is a documented public helper now.
- `plugins/a4/scripts/markdown_validator/frontmatter.py` (580 lines): adds `_validate_task_files` rule. Wired from the main per-file validator after the existing post-draft authoring checks.
- `plugins/a4/scripts/markdown_validator/status_consistency.py` (461 lines): `_fm` shim and local `collect_family` removed; imports `collect_family` from `common` and `read_fm` from `markdown`. `collect_specs` stays as a back-compat alias.
- `plugins/a4/references/frontmatter-schema.md`: deferred item #4 (`task.files:` enforcement) removed; `research` `complete` preflight became item #4.
- `.claude-plugin/marketplace.json` — a4 plugin at `9.7.0`.

## Related Links

- Previous handoff: `.handoff/5-2026-04-30_1303-cascade-trigger-map-and-engine-consolidation.md`. This session executed its Next Steps #1, #2, #3 in order.
- a4 plugin contributor notes: `plugins/a4/CLAUDE.md`.
- Project-root contract: `CLAUDE.md`.
- Schema (single source of truth): `plugins/a4/references/frontmatter-schema.md`. Deferred items section is now down to four entries; `task.files:` enforcement landed this session.
- Task artifact contract: `plugins/a4/references/task-artifacts.md` (unchanged this session, but it is the authoritative prose for the rule landed in commit `222ace36e`).
- No external GitHub issues / PRs; everything in-tree.

## Decisions and Rationale

- **Dry-run gate placement.** Moving the gate from before `_parse` to right before `write_file` keeps the disk-side semantics identical (no writes in dry-run) but exposes parse / rewrite errors during preview. Considered keeping a parse-only short-circuit for performance; rejected — the parse cost is trivial and the safety win (true preview) is worth more.
- **`iter_family` returns a list, not an iterator.** Existing call sites (status_consistency, the new `find_*`) all consume the full sequence. Returning a list avoids generator-exhaustion subtleties when the same call site might iterate twice in a future refactor, and matches the `iter_issue_files` precedent.
- **Keep `collect_family` returning `dict[str, dict]` (no `Path` exposed).** Considered a richer `dict[str, tuple[Path, dict]]` shape that would let callers avoid the second walk for path access. Rejected — would force every existing `items.items()` call site in `status_consistency` (8 places) to update. The lighter approach: `iter_family` for `(path, fm)` callers, `collect_family` for `key→fm` callers.
- **`RefIndex` built once per `transition()` / `sweep()` call.** `RefIndex._build` is `O(N)` over the workspace. For a single-call CLI invocation this is well under the cost of opening the file system. Considered lazy / cached construction; rejected for now — premature optimization, and the current shape is easy to reason about.
- **`_apply_supersedes_chain` keeps a path-form fallback.** When `index.resolve(entry)` returns `None`, falling back to `normalize_ref` preserves the pre-existing distinction between cross-family-by-prefix (skip) and missing-file (error). Without the fallback, an unresolved entry would either crash or silently disappear. The fallback is identical to the pre-RefIndex code path.
- **Deleted `find_usecases_superseded_by`.** Greps confirmed zero callers across the entire repo — defined but unused. The supersedes chain reads the source file's own `supersedes:` list; there is no "which files supersede X" reverse query in any cascade. Per project rule, certain-dead code is deleted rather than retained.
- **Single rule for `task.files:` enforcement (`task-files-bad-artifact-path`).** Considered three separate rules (`not-under-artifacts` / `kind-mismatch` / `id-slug-mismatch`) for sharper error messages. Rejected — the schema documents this as one logical contract, the existing `id-filename-mismatch` precedent uses one rule with a precise detail, and the consolidated detail string ("must start with X or Y") is already actionable.
- **Skip-when semantics in `_validate_task_files`.** When `kind` is missing, `id` is non-int, or filename id-slug doesn't match the frontmatter id, the rule defers entirely. The other rules (`required-field`, `type-mismatch`, `id-filename-mismatch`) already surface those drift modes, and emitting an additional "wrong artifact path" violation on top would just be noise.
- **Marketplace bumps:**
  - 9.6.1 → 9.6.2: dry-run reliability fix → patch.
  - 9.6.2 → 9.6.3: pure refactor with no API change → patch.
  - 9.6.3 → 9.6.4: `#<id>` correctness fix → patch.
  - 9.6.4 → 9.7.0: new validator rule that may flag previously-tolerated drift → minor (project follows pre-1.0-style minor-for-newly-strict-validation).

## Important Dialog

- Topic continuation: user opened handoff 5 at session start; this thread inherits its `topic: a4-validator-hardening`.
- "분리 커밋" (in response to commit-split suggestion for Next Step #2) — confirmed splitting the shared-helper promotion (`5594e4bb4`) and the RefIndex routing (`be65ba90f`) into two commits was the right call. The shared-helper refactor is pure mechanics; the RefIndex routing carries a behavior-changing skip-label preservation and is worth its own diff.
- "진행" (after each commit, then after the smoke tests passed) — user gave the green light to proceed to the next step in the queue without re-discussing scope.
- Project rule (carried forward): "When making function calls using tools that accept array or object parameters ensure those are structured using JSON" (system).
- Korean honorific (존댓말) is the active mode for chat replies; file content stays in English.

## Validation

All commands run from repo root unless noted. Outputs verbatim where short.

- `git status --short` → empty (clean working tree).
- `git log -1 --oneline` → `222ace36e feat(a4): enforce task.files: artifact-path contract`.
- `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`:
  ```
  frontmatter [workspace+file] — YAML schema (required fields, enums, types), path-reference format, wiki `type:` matches filename, id uniqueness.
  status [workspace+file] — Cross-file status consistency — `supersedes` ↔ status, `promoted` ↔ status, UC discard cascades to task / review.
  transitions [workspace+file] — Status transition legality — diff working tree against HEAD via git and reject `status:` jumps not allowed by the family transition table. Safety net for hand edits that bypass `transition_status.py`.
  ```
- Module import sanity:
  ```
  uv run --with pyyaml python -c "
  import sys; sys.path.insert(0, 'plugins/a4/scripts')
  from common import iter_family, collect_family, normalize_ref
  from markdown import read_fm
  from markdown_validator.refs import RefIndex
  from transition_status import find_tasks_implementing, find_reviews_targeting, _apply_supersedes_chain, _apply_reverse_cascade
  from markdown_validator.frontmatter import _validate_task_files
  print('all imports OK')"
  ```
  → `all imports OK`.
- Step #1 dry-run smoke tests (commit `771068c7f`): T1 dry-run leaves disk unchanged on clean transition; T2 real-run writes `status: ready`; T3 dry-run cascade reported with disk unchanged; T4 corrupt FM target was outside cascade scope (cascade pre-parse caught it earlier — fix is still well-formed); T5 corrupt primary frontmatter surfaces error in dry-run. All pass.
- Step #2-A shared-helper smoke tests (commit `5594e4bb4`): T1 list-checks works; T2 shared helpers importable; T3 task cascade discovery via `iter_family` works; T4 review cascade discovery (string + list) via `iter_family` works; T5 sweep over `iter_family` is idempotent (`total_cascades: 1` then `0`); T6 status_consistency drift detection still works. All pass.
- Step #2-B RefIndex cascade smoke tests (commit `be65ba90f`): T1 task implements via `#<id>` resolves and cascades; T2 review target via `#<id>` resolves (string + list); T3 supersedes via `#<id>` resolves and cascades (UC1 needs `shipped` for the chain to fire — initial test setup error caught and fixed); T4 cross-family `#<id>` supersedes detected; T5 bare-slug `<id>-<slug>` implements works; T6 path-form implements still works (no regression); T7 missing supersedes target still errors; T8 sweep over `#<id>` supersedes works. All pass.
- Step #3 task.files smoke tests (commit `222ace36e`): T1 empty `files:` passes; T2 valid feature artifact path passes; T3 valid spike path passes; T4 spike archive path passes; T5 production source path flagged; T6 wrong kind segment flagged; T7 wrong id-slug segment flagged; T8 non-spike with archive-style path flagged; T9 spike with foreign kind flagged; T10 missing kind defers to other rules (no false positive); T11 id-filename mismatch defers to other rules (only `id-filename-mismatch` fires, not the artifact-path rule). All pass.
- No language linter run (Python type-checking is not part of this repo's CI; behavior tests cover the change).

A note on test plumbing: validator violation summary lines emit on **stderr**, not stdout. Smoke test helpers must check `r.stdout + r.stderr` — initial T5-T9 (Step #3) failed only because the helper checked stdout alone. The fix was to combine.

## Known Issues and Risks

- **`research` `complete` initial-status preflight still deferred.** `frontmatter-schema.md` deferred item #4 (was #5) — when `research` is authored at `status: complete` with non-empty `files:`, the static rule now ensures the *shape* is correct, but no script verifies the artifact files actually exist on disk. This is Next Step #1 below.
- **`_apply_supersedes_chain` `RefIndex` fallback can mask `#<id>` drift.** If a `supersedes: ['#999']` entry has no matching id, `index.resolve` returns `None`, the fallback runs, and `normalize_ref('#999')` produces `'#999'` which does not start with `usecase/` → a `cross-family-supersedes` skip is emitted instead of the more accurate "missing target". Pre-existing limitation. Could be sharpened by checking `index.is_id_bearing(entry)` before falling back, but low priority.
- **`_apply_status_change` cascade write still uncaught.** If a cascade target has unreadable frontmatter at write time, `_apply_status_change` raises `RuntimeError` and `transition()` does not catch it for cascade calls. Behavior preserved from the engine consolidation in handoff 5; was a latent bug before the consolidation too. Low likelihood — the engine pre-parses and bails out earlier on `fm is None`.
- **Skip-label format inconsistency persists.** Skipped rows still use `target_kind/<stem>` (no `.md`) for the path while cascade rows use `target_kind/<stem>.md`. Carried forward from earlier handoffs; not behavior-relevant. Tracked as Next Step #2 below.
- **Marketplace 9.7.0 may surface drift in real workspaces.** The new `task-files-bad-artifact-path` rule will fail on any workspace whose `task.files:` lists production source paths or foreign-id artifact paths. The minor bump is the signal; existing workspaces upgrading should expect to clean up these paths (move them to body `## Files` per the schema).

## Next Steps

In priority order. Each is a clean separate commit / PR.

1. **`research` `complete` initial-status preflight.** When `research` is authored at `status: complete` with non-empty `files:`, every artifact path must exist under `artifacts/task/research/<id>-<slug>/` before the writer accepts the file. Fits into the static frontmatter validator next to `_validate_task_files`, or could be a writer-side preflight in `transition_status.py`. Likely the validator since it composes with the existing `task-files-bad-artifact-path` rule. Was Next Step #4 in handoff 5; remains the only deferred item directly tied to `task.files:`.
2. **Standardize skip-label path format.** Decide whether skipped rows in cascade reports should include `.md` (matching cascade rows) or stay bare. Trivial change, stylistic only. Was Next Step #5 in handoff 5.
3. **Sharpen `_apply_supersedes_chain` `#<id>` unresolved diagnostics.** When `index.resolve(entry)` returns `None` for an `#<id>` form, surface "supersedes target missing" instead of "cross-family-supersedes" by checking `index.is_id_bearing(entry)` before falling back to `normalize_ref`. Small UX improvement on the error message.
4. **Workspace-wide a4 in-tree audit.** No `task/*/*.md` files exist in this repo's `a4/` workspace yet, so the new rule wasn't tested against real authored content. When a workspace materializes (or on import from another project), run `validate.py --only frontmatter <a4-dir>` and clean up any `task-files-bad-artifact-path` hits; that may reveal whether the prefix list needs expansion.
5. **Engine error handling: catch cascade `_apply_status_change` exceptions.** Wrap the cascade per-target write in a try/except so an unreadable target frontmatter at write time becomes a `report.errors` entry instead of crashing the script. Low likelihood (pre-parse already filters), but cheap to harden.

## Open Questions

- Should `cascade_for` lookup be exposed to `markdown_validator.transitions` to enrich illegal-transition messages? E.g., if a hand-edit changes `usecase/1.md` from `implementing` to `discarded` (legal), the safety net passes silently — but `cascade_for` would tell us "this transition implies a cascade that did not run." That extra signal could turn a Stop-hook pass into a "did you mean to use `transition_status.py`?" hint. Carried over from handoff 5 — still open.
- Is it worth caching `RefIndex` construction across `sweep()` and a subsequent `transition()` in the same Python process? Currently each `transition()` rebuilds. Negligible for typical CLI use; could matter if a future caller batches transitions. Defer until that caller exists.
- For `task.files:`, should the artifact-path rule allow trailing `.md` paths (a body file under the artifact directory) the same way it allows binary artifacts? Currently any file extension passes as long as the prefix matches. No reason to restrict, but worth confirming if workspaces start mixing markdown notes into artifact dirs.

## Useful Commands and Outputs

```sh
# Inspect this session's commits since handoff 5
git log f5c13b5ed..HEAD --oneline

# Exact diffs for each step
git show 771068c7f    # dry-run true-preview fix
git show 5594e4bb4    # shared helper promotion
git show be65ba90f    # RefIndex cascade resolution
git show 222ace36e    # task.files artifact-path enforcement

# Run all checks against a workspace
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir>

# Run only the frontmatter rules (where the new task-files rule lives)
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir> --only frontmatter

# Happy-path writer (now with #<id>-resolving cascades)
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --to <status> --reason "..."
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --validate --to <status>
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --sweep

# Verify shared helpers and RefIndex flow quickly
uv run --with pyyaml python -c "
import sys; sys.path.insert(0, 'plugins/a4/scripts')
from common import iter_family, collect_family
from markdown import read_fm
from markdown_validator.refs import RefIndex
from transition_status import find_tasks_implementing, find_reviews_targeting
print('all imports OK')
"
```

To reproduce the smoke tests (Step #1 T1-T5, Step #2-A T1-T6, Step #2-B T1-T8, Step #3 T1-T11), see the inline scripts in the conversation transcript before this handoff. Each test creates a temp workspace, plants the scenario (task / review / spec / supersedes chain or `task.files:` shape), and asserts the expected JSON / stderr output. When extending: remember validator violations land on **stderr**, not stdout.
