---
sequence: 7
timestamp: 2026-04-30_1554
timezone: KST +0900
topic: a4-validator-hardening
previous: 6-2026-04-30_1538-dry-run-shared-helpers-and-task-files-enforcement.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1554. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Continue handoff 6's Next Steps, in priority order:

1. Land the `research` `complete` initial-status preflight (handoff 6 Next Step #1) — when a `kind: research` task is at `status: complete` with non-empty `files:`, every entry whose prefix matches `artifacts/task/research/<id>-<slug>/` must point to a file that exists on disk. Closes the only remaining `task.files:`-related deferred item in `frontmatter-schema.md`.
2. Standardize cascade skip-label path format (handoff 6 Next Step #2) — three skip rows in `transition_status.py` were emitting bare `<family>/<stem>` while every cascade row and every other skip row already used `<family>/<stem>.md`.
3. Sharpen `_apply_supersedes_chain`'s `#<id>`-unresolved diagnostics (handoff 6 Next Step #3) — id-bearing forms (`#<id>`, `<family>/<id>`, `<id>-<slug>`) that the index could not resolve were misclassified as `cross-family-supersedes` skips because the path-form fallback did not start with the family prefix.
4. Harden cascade write-time error handling (handoff 6 Next Step #5) — wrap the per-target `_apply_status_change` call in both engines so `RuntimeError` from unreadable / re-parse-failing frontmatter at write time becomes a `report.errors` entry instead of crashing the script.

Handoff 6 Next Step #4 (workspace-wide a4 in-tree audit) is **not actionable in this repo** — no `a4/` workspace exists in-tree.

This thread continues directly from handoff 6 (`a4-validator-hardening`). Starting state: HEAD `222ace36e feat(a4): enforce task.files: artifact-path contract` plus the handoff-6 docs commit (`21883d997`). This session adds four substantive commits and bumps the a4 marketplace from `9.7.0` to `9.8.3`.

## Current State

- Branch: `main`. Working tree clean.
- HEAD: `906060d7d fix(a4): catch cascade write-time RuntimeError in both engines`.
- a4 marketplace version: `9.8.3` (`.claude-plugin/marketplace.json`).
- All three registered checks present: `frontmatter`, `status`, `transitions`. Verified via `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`.
- Module sizes (current): `transition_status.py` 862 lines, `frontmatter.py` 641, `status_consistency.py` 461, `common.py` 128, `markdown.py` 250, `markdown_validator/refs.py` 179.
- `frontmatter-schema.md` "Known deferred items" section is now down to **three entries** — `task.files:` enforcement landed in handoff 6 (`task-files-bad-artifact-path`), and `research` `complete` preflight (`task-files-missing-artifact`) landed this session.
- Static frontmatter rules tied to task artifacts:
  - `task-files-bad-artifact-path` (handoff 6, commit `222ace36e`) — every entry in a task's `files:` must start with `artifacts/task/<kind>/<id>-<slug>/`; `kind: spike` also accepts `artifacts/task/spike/archive/<id>-<slug>/`.
  - `task-files-missing-artifact` (this session, commit `6e5b5b549`) — when `kind: research` is at `status: complete`, every entry whose prefix matches `artifacts/task/research/<id>-<slug>/` must point to an existing file on disk. Layered on top of the shape rule — entries that fail the shape rule defer to it rather than emitting both.
- Cascade reports' `skipped[*].path` field is uniform: every entry now ends in `.md`, matching `cascades[*].path`.
- `_apply_supersedes_chain` splits on `index.is_id_bearing(entry)` for unresolved entries: id-bearing forms become `supersedes target missing` errors; non-id-bearing forms keep the path-form fallback (cross-family skip vs missing-file error).
- Both cascade engines (`_apply_reverse_cascade`, `_apply_supersedes_chain`) wrap the per-target `_apply_status_change` call in `try / except RuntimeError`; failures land on `report.errors` and the cascade row is suppressed.

## Changes Made

This session's commits since handoff 6 (`21883d997`), oldest first. Use `git show <sha>` for exact file-by-file changes.

- `6e5b5b549 feat(a4): preflight research-complete artifact existence` — adds `task-files-missing-artifact` rule via new helper `_validate_research_complete_artifacts(rel_str, fm, path, a4_dir)` in `markdown_validator.frontmatter`. Triggers only when `kind == "research"` and `status == "complete"` with non-empty `files:`. For each entry whose prefix matches `artifacts/task/research/<id>-<slug>/`, checks `(a4_dir.parent / entry).is_file()`. `artifacts/` lives at project root (sibling of `a4/`) per `references/task-artifacts.md`. Skip-when semantics inherit from the shape rule: bad prefixes defer to `task-files-bad-artifact-path`; missing `kind` / non-int `id` / filename id-slug mismatch defer to other rules. Removes deferred item #4 from `frontmatter-schema.md`. Marketplace `9.7.0 → 9.8.0` (minor — newly strict validation).

- `e97f8bc6d refactor(a4): standardize cascade skip-label paths to include .md` — three skip rows in `transition_status.py` were inconsistent with cascade rows:
  - `_apply_reverse_cascade`: `f"{target_kind}/{path.stem}"` → `f"{target_kind}/{path.stem}.md"`.
  - `_apply_supersedes_chain` cross-family-supersedes via `RefIndex`: `resolved.canonical` → `f"{resolved.canonical}.md"`.
  - `_apply_supersedes_chain` cross-family-supersedes via `normalize_ref` fallback: `norm` → `f"{norm}.md"`.

  No behavior change for the writer, cascades, or report shape — strictly the path-label string in `skipped[*].path`. Marketplace `9.8.0 → 9.8.1`.

- `c2051b4dd fix(a4): sharpen #<id>-unresolved diagnostics in supersedes chain` — `_apply_supersedes_chain`'s path-form fallback was misclassifying id-bearing-but-unresolved entries as `cross-family-supersedes` skips. Splits the fallback on `index.is_id_bearing(entry)`:
  - id-bearing & unresolved → `report.errors.append("supersedes target missing: '<entry>' (no file with this id in workspace)")`.
  - non-id-bearing → existing `normalize_ref` path (cross-family-supersedes skip when not under family prefix; missing-target error otherwise).

  Resolved id-bearing entries continue through the existing `if resolved.folder != family` branch (cross-family skip preserved), so cross-family `#<id>` references that *do* resolve still skip correctly. Docstring updated to describe the split. Marketplace `9.8.1 → 9.8.2`.

- `906060d7d fix(a4): catch cascade write-time RuntimeError in both engines` — both cascade engines pre-parse target frontmatter, but `_apply_status_change` re-parses inside, and a target whose first-pass `fm` was salvageable but rewriting blows up (or whose file became unreadable between the two reads) would `raise RuntimeError` and crash the whole script after the primary write already succeeded. Wraps the per-target `_apply_status_change` call in `_apply_reverse_cascade` and `_apply_supersedes_chain` in `try / except RuntimeError`; the exception is appended to `report.errors` and the cascade row is **not** added. Other cascade targets continue. Docstring on `_apply_reverse_cascade` updated to describe the recorded-not-raised contract. Marketplace `9.8.2 → 9.8.3`.

## Key Files

- `plugins/a4/scripts/transition_status.py` (862 lines, +24 / -14 vs handoff 6):
  - `_apply_reverse_cascade` — skip path now `<target_kind>/<stem>.md`; `_apply_status_change` call wrapped in `try / except RuntimeError`.
  - `_apply_supersedes_chain` — cross-family skip path standardized to include `.md` in both the `RefIndex`-resolved branch and the `normalize_ref` fallback branch; fallback now branches on `index.is_id_bearing(entry)`; per-target `_apply_status_change` call wrapped in `try / except RuntimeError`.
  - Docstring on `_apply_supersedes_chain` updated to describe the id-bearing split.
- `plugins/a4/scripts/markdown_validator/frontmatter.py` (641 lines, +61 vs handoff 6):
  - New `_validate_research_complete_artifacts(rel_str, fm, path, a4_dir)` helper.
  - Wired from the main `validate_file` after `_validate_task_files`.
- `plugins/a4/references/frontmatter-schema.md`: deferred items section trimmed to three entries (was four). The `task.files:` enforcement entry from handoff 6 was already gone; this session removed `research` `complete` preflight.
- `plugins/a4/scripts/markdown_validator/refs.py` (179 lines, unchanged this session): `is_id_bearing(ref)` was already public — this session simply started using it from `transition_status.py`.
- `.claude-plugin/marketplace.json` — a4 plugin at `9.8.3`.

## Related Links

- Previous handoff: `.handoff/6-2026-04-30_1538-dry-run-shared-helpers-and-task-files-enforcement.md`. This session executed its Next Steps #1, #2, #3, #5 in order. Next Step #4 (workspace-wide a4 in-tree audit) is not runnable in this repo (no `a4/` workspace).
- a4 plugin contributor notes: `plugins/a4/CLAUDE.md`.
- Project-root contract: `CLAUDE.md`.
- Schema (single source of truth): `plugins/a4/references/frontmatter-schema.md`. Deferred items section is now down to three entries; both `task.files:`-related deferreds have landed.
- Task artifact contract: `plugins/a4/references/task-artifacts.md` (unchanged; authoritative prose for the rules now enforced by `task-files-bad-artifact-path` and `task-files-missing-artifact`).
- No external GitHub issues / PRs; everything in-tree.

## Decisions and Rationale

- **`task-files-missing-artifact` is research-only, layered on the shape rule.** Handoff 6 specifically scoped the deferred item to `research` at `status: complete`. Considered generalizing to all kinds at terminal status (e.g., `feature`/`bug`/`spike` at `complete`) — rejected because (a) the deferred item itself was research-only, and (b) `spike` at `complete` may have artifacts at the archive prefix that complicate the existence check, and (c) the consolidated rule would need its own scope decision before landing. Kept narrow; widening can be a separate rule if a need surfaces.
- **Defer to the shape rule rather than re-emitting on bad prefix.** When an entry's prefix is wrong, `_validate_research_complete_artifacts` skips that entry — `task-files-bad-artifact-path` already names the actionable error. Emitting both ("wrong prefix" *and* "missing on disk") would just be noise. Same skip-when philosophy as the shape rule's deferral on missing `kind` / `id` / filename mismatch.
- **`artifacts/` is at project root (`a4_dir.parent`).** `references/task-artifacts.md` documents the layout: `<project-root>/a4/task/...` parallel to `<project-root>/artifacts/task/...`. The validator already receives `a4_dir`; computing `a4_dir.parent` keeps the path-resolution deterministic without introducing a new "project root" concept.
- **Skip-label `.md` standardization, not `.md` removal.** Two ways to make the skip vs cascade rows uniform: add `.md` to skip rows or strip `.md` from cascade rows. Chose to add — most existing skip rows (already-superseded, not-supersedable, already-at-target) already used `.md`, so the `.md`-bearing form was already the majority and matches the cascade form. Stripping would have touched more lines and changed the user-visible cascade output.
- **`is_id_bearing` split happens in the fallback, not the resolved branch.** The resolved branch already had a correct cross-family-vs-cascade split (`if resolved.folder != family`). The fallback's bug was specific: `normalize_ref('#999')` returned `'#999'`, which does not start with `usecase/`, so it fell into the cross-family bucket. Adding the `is_id_bearing` check **before** `normalize_ref` makes the fallback distinguish "the ref names an id that doesn't exist" (sharp missing-target error) from "the ref is a path-form to a different family or a non-existent file" (existing path-form-handling).
- **Cascade `try / except RuntimeError`, not `except Exception`.** `_apply_status_change` only raises `RuntimeError` (with the explicit `f"{path}: unreadable frontmatter"` message). Catching the narrow type keeps unrelated bugs (e.g., a `KeyError` from rewrite_frontmatter_scalar) loud. Considered catching `Exception` for safety — rejected; if some other exception leaks through, we want a stack trace, not a silent skip.
- **Both engines wrap the call site, not `_apply_status_change` itself.** Wrapping inside `_apply_status_change` would change semantics for the **primary** transition too — and `transition()` already handles primary failures via the existing top-level `try / except RuntimeError` (line ~558 in `transition_status.py`). The cascade engines were the only callers without coverage; wrapping at the call site keeps the engine-vs-primary boundary clean.
- **Marketplace bumps:**
  - `9.7.0 → 9.8.0`: new strict validation rule (`task-files-missing-artifact`) → minor (project follows pre-1.0-style minor-for-newly-strict-validation).
  - `9.8.0 → 9.8.1`: cosmetic skip-label standardization, no behavior change → patch.
  - `9.8.1 → 9.8.2`: diagnostic accuracy fix for unresolved id-bearing supersedes entries → patch.
  - `9.8.2 → 9.8.3`: defensive cascade exception handling, low-likelihood path → patch.

## Important Dialog

- Topic continuation: user opened handoff 6 at session start; this thread inherits its `topic: a4-validator-hardening`.
- "1" — user-typed reply right after handoff 6's Next Steps list was surfaced. Auto mode was active; the assistant proceeded autonomously through Next Steps #1–#3, then later #5, after each smoke-test pass. The assistant flagged at the end that "1" might have been intended as a single-step instruction and offered rollback; user reply was **"다음 작업"** ("next task"), confirming continued autonomous progress.
- "다음 작업" — green light to continue down the queue without re-discussing scope. The assistant then completed handoff 6 Next Step #5 (`906060d7d`).
- Project rule (carried forward): "When making function calls using tools that accept array or object parameters ensure those are structured using JSON" (system).
- Korean honorific (존댓말) is the active mode for chat replies; file content stays in English.

## Validation

All commands run from repo root unless noted. Outputs verbatim where short.

- `git status --short` → empty (clean working tree).
- `git log -1 --oneline` → `906060d7d fix(a4): catch cascade write-time RuntimeError in both engines`.
- `git log 222ace36e..HEAD --oneline`:
  ```
  906060d7d fix(a4): catch cascade write-time RuntimeError in both engines
  c2051b4dd fix(a4): sharpen #<id>-unresolved diagnostics in supersedes chain
  e97f8bc6d refactor(a4): standardize cascade skip-label paths to include .md
  6e5b5b549 feat(a4): preflight research-complete artifact existence
  21883d997 docs(handoff): snapshot a4-validator-hardening session state
  ```
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
  from common import iter_family, collect_family
  from markdown import read_fm
  from markdown_validator.refs import RefIndex
  from markdown_validator.frontmatter import (
      _validate_task_files, _validate_research_complete_artifacts, validate_file
  )
  from transition_status import (
      find_tasks_implementing, find_reviews_targeting,
      _apply_supersedes_chain, _apply_reverse_cascade,
  )
  print('all imports OK')"
  ```
  → `all imports OK`.
- Step #1 `task-files-missing-artifact` smoke tests (commit `6e5b5b549`): 8 cases — T1 complete + existing artifact passes; T2 complete + missing flagged; T3 status≠complete skipped; T4 kind≠research skipped; T5 empty `files:` passes; T6 wrong-prefix entry defers to shape rule (not double-flagged); T7 partial existence (one exists, one missing) flags only the missing; T8 directory path (not a file) flagged. All pass.
- Step #2 skip-label `.md` standardization smoke tests (commit `e97f8bc6d`): 5 cases — T1 review-terminal skip path ends in `.md`; T2 already-discarded skip path ends in `.md`; T3 cross-family-supersedes skip path ends in `.md`; T4 already-at-target skip path ends in `.md` (was already `.md` because `rel_path` carries the suffix; verified no regression); T5 cascade row still ends in `.md` (regression check). All pass.
- Step #3 id-bearing diagnostic sharpening smoke tests (commit `c2051b4dd`): 5 cases — T1 unknown `#<id>` short-form → `supersedes target missing` error, **not** cross-family-supersedes skip; T2 unknown `usecase/<id>` slug-less form → missing-target error; T3 resolved `#<id>` still cascades correctly (regression check); T4 resolved cross-family `#<id>` still emits cross-family-supersedes skip (regression check); T5 non-id-bearing missing target still produces error or cross-family skip (existing path-form path preserved). All pass.
- Step #4 cascade write-time exception smoke tests (commit `906060d7d`): 4 cases — T1 happy-path UC-discarded cascade unaffected by try/except; T2 supersedes-chain happy path unaffected; T3 monkey-patched `_apply_status_change` to raise → `_apply_reverse_cascade` records error in `report.errors`, no cascade row appended; T4 same monkey-patch applied to `_apply_supersedes_chain` → error recorded, no cascade row. All pass.
- Test plumbing note (carried from handoff 6): the smoke-test helpers for Step #1 use `r.stdout + r.stderr` because validator violation summary lines emit on **stderr**, not stdout. Steps #2–#4 talk to `transition_status.py --json` which emits the JSON report on stdout, so they use `stdout` only.
- No language linter run (Python type-checking is not part of this repo's CI; behavior tests cover the change).

## Known Issues and Risks

- **`research` `complete` preflight is research-only.** `feature`/`bug`/`spike` at `complete` with `files:` listing missing artifacts will pass the validator. The shape rule still catches wrong-prefix paths for all kinds, but on-disk existence is verified for `research` only. Widening is a candidate for a follow-up (see Open Questions).
- **`research` `complete` preflight assumes `artifacts/` at `a4_dir.parent`.** Workspaces that place `a4/` at a non-standard depth (e.g., a nested project layout) would compute the wrong project root. The schema does not formally pin `a4/` to a project root, so this is a soft assumption derived from `references/task-artifacts.md`.
- **Cascade `RuntimeError` catch is narrow.** Catches `RuntimeError` only — not `Exception`. If `rewrite_frontmatter_scalar` ever starts raising a different exception type (e.g., a YAML library error), the engine would crash again. Trade-off described in *Decisions and Rationale*.
- **Marketplace 9.8.0 may surface drift in real workspaces.** The new `task-files-missing-artifact` rule will fail on any workspace whose `research` tasks at `status: complete` list artifacts that are not yet committed. The `9.7.0 → 9.8.0` minor bump is the signal.
- **Workspace audit still pending.** No `task/*/*.md` files exist in this repo's `a4/` workspace yet, so neither the new `task-files-missing-artifact` rule nor the artifact-shape rule has been exercised against authored content. Authoring drift could still hide.
- **Handoff 6's "supersedes target missing" error format change is potentially breaking.** Tools or eyeballs that grep for the exact old `supersedes target missing: <path>.md` string now also need to handle the new id-bearing form: `supersedes target missing: '#<id>' (no file with this id in workspace)`. The non-id-bearing path-form message is unchanged.

## Next Steps

In priority order. Each is a clean separate commit / PR.

1. **Workspace-wide a4 in-tree audit (carried from handoff 6 #4).** When a workspace materializes (or on import from another project), run `validate.py --only frontmatter <a4-dir>` and triage hits for `task-files-bad-artifact-path` and `task-files-missing-artifact`. May reveal whether the `research`-only scope of the existence check should widen to `feature` / `bug` (and how to handle `spike` archive paths).
2. **Decide whether to widen `task-files-missing-artifact` to `feature` and `bug`.** At `status: complete`, a feature/bug task whose `files:` lists missing artifacts is in the same drift mode. The `spike` case is harder — `complete` may have happened **before** archive, so the path may legitimately point at the original location until `git mv`. Either widen partially (`feature` and `bug` only) or design the spike-archive transition story before widening.
3. **Cascade `cascade_for` enrichment in transition-legality safety net.** Carried from handoff 6 Open Questions: should `cascade_for` lookup be exposed to `markdown_validator.transitions` to enrich illegal-transition messages? E.g., a hand-edit `usecase/1.md` `implementing → discarded` is legal but skips cascades; surfacing "this transition implies a cascade that did not run" would turn a Stop-hook pass into a "use `transition_status.py`?" hint.
4. **`task-files-bad-artifact-path` and `task-files-missing-artifact` representation in the schema enforcement table.** `references/frontmatter-schema.md` "Schema enforcement" table does not yet list either rule by name. Adding rows would keep the table authoritative, matching the precedent set by `placeholder-in-title`, `id-filename-mismatch`, etc. Trivial doc patch.
5. **Consider catching broader exceptions in cascade write paths.** The narrow `RuntimeError` catch protects against the known case (`_apply_status_change` raising on unreadable FM). If a future refactor changes the exception type, the engine crashes. Either: (a) document the contract in `_apply_status_change`'s docstring, or (b) widen to `except Exception as e` and rely on `report.errors` carrying the type name. Low priority.

## Open Questions

- **Should `task-files-missing-artifact` extend to `kind: feature` and `kind: bug`?** They share the same artifact contract; only `spike` archive complicates the picture. Worth deciding before the next workspace import. (See Next Steps #2.)
- **Should `cascade_for` be exposed to the transitions safety net?** Carried from handoff 6 — still open.
- **Should the artifact-path rules tolerate both `<id>-<slug>` and `<id>-<old-slug>` after a slug rename?** Currently the path's `<id>-<slug>` segment must match the file's actual stem exactly. If a slug renames, the artifact directory has to be `git mv`'d to match. This is consistent with the path-reference forward-stability story but creates a small migration tax. No current pain — flag if it surfaces.
- **Is it worth caching `RefIndex` construction across `sweep()` and a subsequent `transition()` in the same Python process?** Carried from handoff 6 — still open.

## Useful Commands and Outputs

```sh
# Inspect this session's commits since handoff 6
git log 21883d997..HEAD --oneline

# Exact diffs for each step
git show 6e5b5b549   # research complete preflight (task-files-missing-artifact)
git show e97f8bc6d   # skip-label .md standardization
git show c2051b4dd   # #<id>-unresolved diagnostic sharpening
git show 906060d7d   # cascade write-time RuntimeError catch

# Run all checks against a workspace
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir>

# Run only the frontmatter rules (where both task.files: rules live)
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir> --only frontmatter

# Happy-path writer (cascade engines now both catch RuntimeError on per-target writes)
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --to <status> --reason "..."
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --validate --to <status>
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --sweep
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --to <status> --reason "..." --json --dry-run

# Verify shared helpers, RefIndex flow, and the new validator helper quickly
uv run --with pyyaml python -c "
import sys; sys.path.insert(0, 'plugins/a4/scripts')
from common import iter_family, collect_family
from markdown import read_fm
from markdown_validator.refs import RefIndex
from markdown_validator.frontmatter import (
    _validate_task_files, _validate_research_complete_artifacts
)
from transition_status import (
    find_tasks_implementing, find_reviews_targeting,
    _apply_supersedes_chain, _apply_reverse_cascade,
)
print('all imports OK')
"
```

To reproduce the smoke tests (Step #1 T1–T8, Step #2 T1–T5, Step #3 T1–T5, Step #4 T1–T4), see the inline scripts in the conversation transcript before this handoff. Each test creates a temp workspace, plants the scenario (research task + artifact dir, or supersedes chain, or cascade target with monkey-patched `_apply_status_change`), and asserts the expected JSON / stderr output. When extending: validator violations land on **stderr**; `transition_status.py --json` reports land on **stdout**.
