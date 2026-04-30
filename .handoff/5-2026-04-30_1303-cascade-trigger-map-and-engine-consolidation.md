---
sequence: 5
timestamp: 2026-04-30_1303
timezone: KST +0900
topic: a4-validator-hardening
previous: 4-2026-04-30_1229-a4-validator-hardening-and-status-model-canonical.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1303. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Continue Next Steps #1-#3 from handoff 4: (1) promote the cascade trigger map into `status_model.py` with a `cascade_for()` lookup helper, then (2) drop the duplicate post-draft validation that `transition_status.py` runs in parallel with `markdown_validator.frontmatter`, and (3) consolidate the four `_cascade_*` functions into a two-helper engine. Each as its own clean commit.

This thread continues directly from handoff 4 (`a4-validator-hardening`). The starting state was the centralization of `SUPERSEDES_TRIGGER_STATUS` / `TASK_RESET_*` / `REVIEW_TERMINAL` plus legality predicates into `status_model.py` (commit `276c216c2`); this session adds the cascade-name dispatch table, removes the writer's duplicated authoring-shape checks, and collapses the four cascade implementations.

## Current State

- Branch: `main`. Working tree clean.
- HEAD: `d3f1142e7 refactor(a4): consolidate cascade functions into a two-helper engine`.
- a4 marketplace version: `9.6.1` (`.claude-plugin/marketplace.json`).
- All three registered checks present: `frontmatter`, `status`, `transitions`. Verified via `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`.
- `transition_status.py` is now 837 lines (was 1011 at start of handoff 4 → 968 after the post-draft drop step → 837 after engine consolidation). Net `-174` lines this session.
- Cascade dispatch is now data-driven: `cascade_for(family, from, to) -> str | None` looks up `CASCADE_TRIGGERS` and a flat `_run_cascade(name, ...)` function dispatches to the two engines.

## Changes Made

This session's commits since handoff 4 (`5931aa55b`), oldest first. Use `git show <sha>` for exact file-by-file changes.

- `e5d0179fd refactor(a4): promote cascade trigger map into status_model` — adds `CASCADE_TRIGGERS: dict[tuple[str, str | None, str], str]` and a `cascade_for(family, from, to) -> str | None` helper to `status_model.py`. Specific `(family, from, to)` keys take precedence over generic `(family, None, to)` wildcards. Replaces the family-specific if/elif cascade dispatch in `transition()` (L708-721) with a flat `cascade_for(...)` lookup + name-keyed dispatch. Marketplace 9.5.1 → 9.5.2.
- `e68979391 fix(a4): handle list-form review target in UC discard cascade` — `transition_status.find_reviews_targeting` was matching only string-scalar `target:`, so reviews with list-form `target:` were silently skipped during UC `→ discarded` cascades. Now mirrors the dual-shape handling already in `status_consistency.check_discarded_cascade`. The pre-existing `missing-discarded-status-review` static drift was the only thing surfacing the gap. Marketplace 9.5.2 → 9.5.3. Resolves handoff 4 Next Step #1.
- `26f20a75a refactor(a4)!: drop duplicate post-draft validation from transition_status` — removes `validate_transition`, `_validate_revising_to_ready`, `_validate_draft_to_active`, `PLACEHOLDER_TOKENS`, `_placeholder_in`, `_is_non_empty_list`, the `--force` CLI flag and `force: bool` parameter on `transition()`, the `Report.validation_issues` field (and its `--json` payload key + `_print_report_human` line), and the now-unused `from typing import Any` import. The same invariants are statically enforced by `markdown_validator.frontmatter` rules `missing-actors-post-draft` and `placeholder-in-title` at the Stop hook. Module docstring + `--validate` help text + three docs (`workspace-assistant.md`, `extract-and-write.md`, `discard.md`) updated to point at the frontmatter validator and reframe exit-2 as "re-author upstream" instead of "retry with --force". `--force` had zero in-tree callers; every doc that mentioned it explicitly forbade its use. **BREAKING.** Marketplace 9.5.3 → 9.6.0. Resolves handoff 4 Next Step #2 with `-99` lines.
- `d3f1142e7 refactor(a4): consolidate cascade functions into a two-helper engine` — replaces `_cascade_uc_revising`, `_cascade_uc_discarded`, `_cascade_uc_shipped`, `_cascade_spec_active` with two engines:
  - `_apply_reverse_cascade(a4_dir, targets, target_kind, skip_when, to_status, reason_text, today, dry_run, report)` — generic walker for reverse-link cascades. Takes a `skip_when(current) -> (reason, detail) | None` predicate; handles parsing, skip recording, status flip, and `Change` row uniformly.
  - `_apply_supersedes_chain(a4_dir, family, rel_path, today, dry_run, report)` — same-family supersedes walker parameterised by `family`, sourcing trigger and supersedable-from sets from `status_model`.
  
  `transition()` calls `_run_cascade(cascade_name, ...)` which dispatches via three lambdas (one per cascade name) capturing per-cascade gate / target / reason. `sweep()` collapses its two near-duplicate UC/spec loops into a single `(family, trigger)` tuple loop calling the supersedes engine directly. One intended label change: UC chain skip reason `not-terminal-active` → `not-supersedable`, matching the spec chain and `references/spec-authoring.md`'s existing usage. Marketplace 9.6.0 → 9.6.1. Resolves handoff 4 Next Step #3 with `-131` lines.

## Key Files

- `plugins/a4/scripts/status_model.py` — canonical home now also for `CASCADE_TRIGGERS` and `cascade_for(family, from_status, to_status)`. Module docstring lists every consumer module (transition_status, markdown_validator.{frontmatter, transitions, status_consistency}, workspace_state, search). Wildcard semantics: specific `(family, from, to)` entries beat generic `(family, None, to)`.
- `plugins/a4/scripts/transition_status.py` — 837 lines. Contains:
  - `_apply_reverse_cascade` (engine for revising / discarded-task / discarded-review)
  - `_apply_supersedes_chain` (engine for UC shipped / spec active)
  - `_run_cascade(name, ...)` (flat dispatch from `cascade_for()`)
  - `transition()` (legality + atomic write + cascade)
  - `sweep()` (idempotent supersedes recovery; single loop over `(usecase, "shipped")` and `(spec, "active")`)
  - `--validate` mode (legality only — no longer runs authoring-shape checks)
  - No `--force` flag; no `validation_issues` anywhere.
- `plugins/a4/scripts/markdown_validator/frontmatter.py` — sole owner of post-draft authoring invariants now (`missing-actors-post-draft`, `placeholder-in-title`). Was already a Stop-hook check in handoff 4.
- `plugins/a4/agents/workspace-assistant.md` — `--force` mention removed; failure messaging reframed to "re-author upstream" rather than "retry with --force".
- `plugins/a4/skills/spec/references/extract-and-write.md` — same reframe; `validation_issues` reference replaced with `errors`.
- `plugins/a4/skills/task/references/discard.md` — same reframe.
- `.claude-plugin/marketplace.json` — a4 plugin at `9.6.1`.

## Related Links

- Previous handoff: `.handoff/4-2026-04-30_1229-a4-validator-hardening-and-status-model-canonical.md`. This session executed Next Steps #1, #2, #3 from that handoff in order.
- a4 plugin contributor notes: `plugins/a4/CLAUDE.md`.
- Project-root contract: `CLAUDE.md`.
- No external GitHub issues / PRs; everything in-tree.

## Decisions and Rationale

- **Cascade trigger fact data, behavior code.** The `CASCADE_TRIGGERS` map encodes only the "(family, from, to) → cascade_name" trigger fact in `status_model.py`; cascade behavior (reverse-link discovery, write, skip semantics) stays in `transition_status.py`. Considered putting `{trigger: callable}` directly in `status_model` but rejected: it would split data and side-effecting code across modules. The current shape lets the markdown_validator look up "this transition triggers a cascade" without dragging the writer's IO surface into the validator.
- **Wildcard `from` for trigger keys.** UC `→ discarded` and UC `→ shipped` are legal from multiple sources, but the cascade is the same regardless. `(family, None, to)` wildcards capture this; specific `(family, from, to)` entries (UC `implementing → revising`) override. Lookup precedence is enforced inside `cascade_for`.
- **`--force` removed entirely (BREAKING).** Open Question #1 from handoff 4 answered. Grep across `plugins/a4/` confirmed zero in-tree callers and that every doc explicitly forbade `--force`. Removal collapses the writer's responsibility to legality + atomic write + cascade, with authoring shape owned by the frontmatter validator. Argparse rejects `--force` with `unrecognized arguments` now — verified.
- **Skip reason unification: `not-terminal-active` → `not-supersedable`.** The UC supersedes chain previously used `not-terminal-active` while the spec chain used `not-supersedable`. The spec doc (`references/spec-authoring.md` L56) already uses `not-supersedable` for both directions in prose. Grep confirmed no consumers checked the old string. Unified on `not-supersedable` for both chains in the engine — minor user-visible label change.
- **Engine shape: predicate-driven reverse cascade.** Considered passing `(family_set_to_skip, skip_reason)` data parameters but the three reverse cascades have semantically different skip logic (set membership vs equality vs terminal-set membership). Lambda predicates at the call site read clearer than over-parameterized data. Each lambda is 1-3 lines.
- **Sweep idempotency preserved.** Original sweep manually injected `from_status="implementing"` (UC) and `from_status="draft"` (spec) to satisfy the now-removed cascade gates. The new `_apply_supersedes_chain` has no such gate (the legality table already restricts when chains can fire from a real transition; sweep is recovery, not transition), so the fake gate value disappears.
- **`Any` re-imported.** Previous commit removed `from typing import Any` as unused; this commit re-adds it (and `Callable`) for the engine's type annotations. Stylistically matches the rest of the repo (`workspace_state.py`, `frontmatter.py`).
- **Patch vs minor bumps:**
  - 9.5.1 → 9.5.2: refactor (adds new module API but doesn't change behavior) → patch.
  - 9.5.2 → 9.5.3: bug fix → patch.
  - 9.5.3 → 9.6.0: BREAKING removal of `--force` → minor (project follows pre-1.0-style minor-for-breaking; actual semver would be major).
  - 9.6.0 → 9.6.1: pure refactor with one trivial label change → patch.

## Important Dialog

- Topic continuation: user opened handoff 4 at session start; this thread inherits its `topic: a4-validator-hardening`.
- "Cascade trigger 테이블 논의" — led to the analysis-then-implement flow for `CASCADE_TRIGGERS` (commit `e5d0179fd`). User accepted the "data only, behavior stays" recommendation.
- "제안대로 진행" (in response to commit-split suggestion) — split status_model + dispatch refactor into one commit and the find_reviews_targeting bug fix into a separate commit.
- "--force grep 결과부터" — user wanted evidence before approving the `--force` removal. Grep across `plugins/a4/` found zero callers, all docs forbade use; user accepted removal.
- Project rule (carried forward): "When making function calls using tools that accept array or object parameters ensure those are structured using JSON" (system).
- Korean honorific (존댓말) is the active mode for chat replies; file content stays in English.

## Validation

All commands run from repo root unless noted. Outputs verbatim where short.

- `git status --short` → empty (clean working tree).
- `git log -1 --oneline` → `d3f1142e7 refactor(a4): consolidate cascade functions into a two-helper engine`.
- `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`:
  ```
  frontmatter [workspace+file] — YAML schema (required fields, enums, types), path-reference format, wiki `type:` matches filename, id uniqueness.
  status [workspace+file] — Cross-file status consistency — `supersedes` ↔ status, `promoted` ↔ status, UC discard cascades to task / review.
  transitions [workspace+file] — Status transition legality — diff working tree against HEAD via git and reject `status:` jumps not allowed by the family transition table. Safety net for hand edits that bypass `transition_status.py`.
  ```
- Cascade engine smoke tests (commit `d3f1142e7`):
  - **T1** UC `implementing → revising` with mixed task statuses (progress / failing / pending / discarded). Cascades: progress → pending, failing → pending. Skips: pending and discarded both with `task-not-in-reset-state`. Pass.
  - **T2** UC `* → discarded` with mixed targets. Cascades: progress / failing / pending tasks → discarded; open string-form and list-form reviews → discarded. Skips: already-discarded task (`already-discarded`); resolved review (`review-terminal`). Pass.
  - **T3** UC `implementing → shipped` with `supersedes: ['usecase/9-prior']`. UC #9 shipped → superseded. Pass.
  - **T4** spec `draft → active` with `supersedes: ['spec/10-old']`. Spec #10 active → superseded. Pass.
  - **T5** spec `draft → active` with cross-family `supersedes: ['usecase/1-foo']`. Skipped with `cross-family-supersedes`. Pass.
  - **T6** UC `implementing → shipped` superseding a UC at `draft`. Skipped with new unified label `not-supersedable`. Pass (intended label change).
  - **T7** `--sweep` first run flips one chain target; second run reports `OK — no supersedes cascades needed.`. Idempotent. Pass.
  - **T8** `--dry-run` on `revising` cascade: prints `(dry-run) ...` for primary + cascade lines; on-disk statuses unchanged before vs after. Pass.
  - **T9** Illegal transition (`shipped → ready`) rejected with rc=2 and the Allowed-from list. Pass.
  - **T10** `--json --dry-run` payload contains keys `['a4_dir', 'cascades', 'current_status', 'dry_run', 'errors', 'family', 'file', 'ok', 'primary', 'skipped', 'target_status']`. **No `validation_issues` key** (confirms commit `26f20a75a`). Pass.
- Step #2 standalone smoke tests (commit `26f20a75a`): cascades unchanged, `--validate` legal/illegal still rc 0/2, `missing-actors-post-draft` and `placeholder-in-title` surface from frontmatter validator at Stop hook, `--force` errors with argparse `unrecognized arguments`. All pass.
- Step #1 standalone smoke tests (commit `e68979391`): five reviews under one UC discard — string-form / list-form single / list-form multi-entry matching / list-form non-matching / list-form already-resolved. First three flip; last two correctly left alone. Pass.
- Module import sanity: `import transition_status` succeeds; `Report` fields are `['a4_dir', 'file', 'family', 'current_status', 'target_status', 'primary', 'cascades', 'skipped', 'errors', 'dry_run', 'ok']` (no `validation_issues`); engines `_apply_reverse_cascade` and `_apply_supersedes_chain` exposed at module level.
- No language linter run (Python type-checking is not part of this repo's CI; behavior tests cover the change).

## Known Issues and Risks

- **`#<id>` shorthand still doesn't work in cascade target discovery.** `find_tasks_implementing` / `find_reviews_targeting` / `find_usecases_superseded_by` use `normalize_ref` directly which only path-strips `.md`; it does not resolve `#<id>` via `RefIndex`. Effect: a workspace authored entirely in `#<id>` style will see `transition_status.py` cascades silently miss targets (the static `status_consistency` checks flag the resulting drift via `missing-…-status-…` violations, so the workflow degrades gracefully). Pre-existing limitation surfaced during smoke testing in handoff 4. Fix candidate is Next Step #2 below (lift target discovery onto the `RefIndex` layer).
- **`_apply_status_change` `--dry-run` short-circuits before parse/write.** Currently, dry-run returns early so dry-run will not surface errors that a real run would (e.g., unreadable target frontmatter). Move the gate to right before `path.write_text` so dry-run becomes a true preview. Identified in handoff 4 Next Step #4, not addressed in this session.
- **Engine error handling: cascade `_apply_status_change` is uncaught.** If a cascade target has unreadable frontmatter at write time, `_apply_status_change` raises `RuntimeError` and `transition()` does not catch it — the script crashes. Behavior preserved from the original `_cascade_*` functions; was a latent bug there too. Low likelihood (the engine pre-parses and bails out earlier on `fm is None`).
- **Skip-label format inconsistency persists.** Skipped rows use `target_kind/<stem>` (no `.md`) for the path, while cascade rows use `target_kind/<stem>.md`. Carries forward from the original cascade functions; not behavior-relevant (humans read either fine, JSON consumers don't normalize) but worth noting if a future cleanup standardizes.
- **`--force` removal is BREAKING for any out-of-tree caller.** No in-tree callers exist; external skills or scripts that passed `--force` now error with argparse `unrecognized arguments`. Documented in commit message as `BREAKING:`.
- **`transition_status.find_reviews_targeting` and the static `status_consistency.check_discarded_cascade` now duplicate dual-shape `target:` handling.** Step #5 below (lifting `collect_family` to a shared layer) would unify both.

## Next Steps

In priority order. Each is a clean separate commit / PR.

1. **Sharpen `--dry-run` semantics in `transition_status._apply_status_change`.** Move the dry-run early-return to right before `path.write_text` so dry-run actually parses and validates everything a real run would. Small, user-visible reliability win. Was Next Step #4 in handoff 4. Add a smoke test where dry-run on a target with unreadable frontmatter surfaces the error (currently silently passes).
2. **Lift `collect_family(a4_dir, family)` and `read_fm(path)` to shared layers, and route cascade target discovery through `RefIndex`.** Two parts:
   - `collect_family` to `common.py` (or `markdown_validator/refs.py`); `read_fm` to `markdown.py`. Then rewrite `find_tasks_implementing` / `find_reviews_targeting` / `find_usecases_superseded_by` against `collect_family`. Shared with `status_consistency.collect_family`.
   - While there, accept `RefIndex`-resolved target identities so `#<id>` shorthand resolves correctly during cascade discovery. This eliminates the only known correctness gap in cascades on `#<id>`-style workspaces.
   Was Next Step #5 in handoff 4 (without the RefIndex piece).
3. **Decide on `task.files:` artifact-path enforcement** — per-kind prefix + id-vs-path consistency. Static check, fits next to existing path-format validation in `frontmatter.py`. Was Next Step #6 in handoff 4.
4. **`research` `complete` initial-status preflight** — path existence on `files:` for `kind: research` at `status: complete`. Was Next Step #7 in handoff 4.
5. **Standardize skip-label path format.** Decide whether skipped rows should include `.md` (matching cascade rows) or stay bare. Trivial change, stylistic only.

## Open Questions

- Should `cascade_for` lookup be exposed to `markdown_validator.transitions` to enrich illegal-transition messages? E.g., if a hand-edit changes `usecase/1.md` from `implementing` to `discarded` (legal), the safety net passes silently — but `cascade_for` would tell us "this transition implies a cascade that did not run." That extra signal could turn a Stop-hook pass into a "did you mean to use `transition_status.py`?" hint. Not done here; would be its own commit.
- The cascade engine's `skip_when` lambdas live at the call site in `_run_cascade`. Acceptable readability for three cases. If a fourth reverse cascade is added in the future, would migrating to small named predicate functions improve readability? Defer until the fourth case.
- `_apply_supersedes_chain` accepts `family` as a free string. Could it instead take a small `SupersedesChainSpec` dataclass that encapsulates the family prefix + supersedable-from set, with `status_model` exporting two singletons? Possibly cleaner, but adds a layer for two consumers. Defer until a third chain appears.

## Useful Commands and Outputs

```sh
# Inspect this session's commits since the previous handoff
git log 5931aa55b..HEAD --oneline

# Exact diffs for each step
git show e5d0179fd    # cascade trigger map → status_model
git show e68979391    # find_reviews_targeting list-form fix
git show 26f20a75a    # drop duplicate post-draft validation (BREAKING --force removal)
git show d3f1142e7    # cascade engine consolidation

# Run all checks against a workspace
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir>

# Happy-path writer
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --to <status> --reason "..."
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --validate --to <status>
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --sweep

# Verify cascade_for() lookup quickly
uv run --with pyyaml python -c "
import sys; sys.path.insert(0, 'plugins/a4/scripts')
from status_model import cascade_for
for case in [('usecase','implementing','revising'),('usecase','ready','discarded'),('usecase','implementing','shipped'),('spec','draft','active'),('usecase','draft','ready')]:
    print(case, '->', cascade_for(*case))
"
```

To reproduce the cascade engine smoke tests (T1-T10), see the inline scripts in the conversation transcript before this handoff. The setup creates a temp git repo with one UC, four implementing tasks at varied statuses (progress / failing / pending / discarded), three reviews (string / list / resolved targets), and an additional `supersedes` chain UC pair, then exercises each cascade path.
