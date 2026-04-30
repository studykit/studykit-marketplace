---
sequence: 4
timestamp: 2026-04-30_1229
timezone: KST +0900
topic: a4-validator-hardening
previous: 3-2026-04-29_2250-markdown-headings-shipped-frontmatter-split-next.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1229. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Harden the a4 validator stack so workspace drift is caught statically (post-draft authoring invariants, id checks, revising-cascade drift), add a Stop-hook safety net that catches direct `status:` edits bypassing `transition_status.py`, and consolidate cascade/transition data into `status_model.py` as the single canonical source — with `transition_status.py` retained as the writer for the happy path.

This thread continues out of an earlier same-session arc (frontmatter-schema decomposition, drift-detector / `[[wikilink]]` removal, validator unification under `markdown_validator/`, `#<id>` reference shorthand) but pivots cleanly to validator hardening from `af0c891f7` onward, which is why the topic is new.

## Current State

- Branch: `main`. Working tree clean.
- HEAD: `276c216c2 refactor(a4): centralize cascade-target data and legality predicates in status_model`.
- a4 marketplace version: `9.5.1` (`.claude-plugin/marketplace.json`).
- All three registered checks present: `frontmatter`, `status`, `transitions`. Verified via `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`.
- `transition_status.py` kept (deletion considered, then rejected — see Decisions). New `markdown_validator.transitions` is the safety net, not a replacement.

## Changes Made

This session's commits since the last handoff (`ea4ada2a1`), oldest first. Two arcs: an earlier frontmatter-schema / convention-cleanup arc, then the validator-hardening arc that defines this topic. Use `git show <sha>` for exact file-by-file changes.

Earlier arc (frontmatter schema decomposition, old-convention removal, `#<id>` shorthand):
- `208815ffa refactor(a4): extract idea authoring contract into idea-authoring.md`
- `5c6355019 refactor(a4): drop close-guard duplication from §Review in frontmatter-schema`
- `f4444a894 refactor(a4): slim §Spec in frontmatter-schema; lifecycle/body lives in spec-authoring.md`
- `dc2970340 refactor(a4): slim §Use case in frontmatter-schema; lifecycle lives in usecase-authoring.md`
- `71641606e refactor(a4): slim §Task and extract cross-kind artifacts into task-artifacts.md`
- `7d940ccf8 refactor(a4): extract brainstorm authoring; remove §Body sections per type table`
- `3c7e39a4c chore(a4): bump to 7.1.0 for frontmatter-schema decomposition`
- `2e67d99bf ignore *.lock file`
- `77310b3ab docs(a4): drop validator-as-tool mentions from conceptual docs`
- `c43b71c1c docs(a4): drop XSD references from references/, skills/, rules/`
- `c970cd133 refactor(a4)!: delete XSD body schemas and the scripts that fed them`
- `aafa88d04 feat(a4)!: drop drift convention, unify validators, add #<id> ref shorthand` — biggest single commit; folds old `validate_frontmatter.py` / `validate_status_consistency.py` into `markdown_validator/` package, deletes `drift_detector.py` + `/a4:drift` skill, removes `[[wikilink]]` + `## Changes` convention, introduces `RefIndex` resolver and `unresolved-ref` rule. Marketplace 9.0.0 → 9.1.0 here.

Validator-hardening arc (this handoff's topic):
- `af0c891f7 feat(a4): validate document id on stop hook` — frontmatter-schema id-filename consistency check (`id-filename-mismatch`).
- `48f45c563 chore(a4): delete unused extract_section.py` — dead-code drop.
- `33bbe13a9 feat(a4): detect revising-cascade drift on tasks` — new `check_revising_cascade` in `status_consistency.py` flags `task.status` in {`progress`, `failing`} when an implementing UC is at `revising` (rule `missing-pending-status-task`).
- `adf947e98 feat(a4): post-draft authoring invariants in frontmatter validator` — adds rules `missing-actors-post-draft` (UC `>= ready` with empty `actors:`) and `placeholder-in-title` (UC `>= ready` or spec `>= active` with `TBD`/`???`/`<placeholder>`/`<todo>`/`TODO:` in `title:`). `POST_DRAFT_STATUSES` and `PLACEHOLDER_TOKENS` added to `frontmatter.py`.
- `6e8291ac2 feat(a4): transition-legality safety net for direct status edits` — new module `markdown_validator/transitions.py` diffs working tree `status:` against HEAD via `git show HEAD:<rel>` and flags transitions outside `FAMILY_TRANSITIONS` for the four writer families (usecase / task / review / spec). Wired into Stop hook (`a4_hook.py _stop`) so edited files are checked at session end. Registered in `markdown_validator/registry.py` as the third check (`transitions`). New `extract_preamble_from_text(text)` helper added to `markdown.py` (used to parse `git show` stdout). Marketplace 9.4.0 → 9.5.0.
- `276c216c2 refactor(a4): centralize cascade-target data and legality predicates in status_model` — moves `SUPERSEDES_TRIGGER_STATUS`, `SUPERSEDABLE_FROM_STATUSES`, `TASK_RESET_ON_REVISING`, `TASK_RESET_TARGET`, `REVIEW_TERMINAL` into `status_model.py`; adds predicates `is_transition_legal`, `legal_targets_from`, `is_terminal`. Updates `transition_status.py`, `status_consistency.py`, and `transitions.py` to import these instead of inlining literal sets and `FAMILY_TRANSITIONS.get(...)` lookups. Behavior identical (see Validation). Marketplace 9.5.0 → 9.5.1 (patch — pure refactor).

## Key Files

- `plugins/a4/scripts/status_model.py` — canonical home now also for `SUPERSEDES_TRIGGER_STATUS`, `SUPERSEDABLE_FROM_STATUSES`, `TASK_RESET_ON_REVISING`, `TASK_RESET_TARGET`, `REVIEW_TERMINAL`, `is_transition_legal`, `legal_targets_from`, `is_terminal`. Module docstring lists every consumer module.
- `plugins/a4/scripts/markdown_validator/transitions.py` — git-diff-based legality safety net; entry points `check_files(a4_dir, files)`, `run_workspace(a4_dir)`, `run_file(a4_dir, file)`. Skips: new files (no HEAD), `idea` / `spark` (absent from `FAMILY_TRANSITIONS`), unchanged status, non-string status.
- `plugins/a4/scripts/markdown_validator/status_consistency.py` — `check_superseded`, `check_discarded_cascade`, `check_revising_cascade`, `check_promoted`. Now imports cascade constants from `status_model`. Local `SUPERSEDES_FAMILIES` is an alias of `SUPERSEDES_TRIGGER_STATUS` to keep call sites stable.
- `plugins/a4/scripts/markdown_validator/frontmatter.py` — schema validator. Adds `POST_DRAFT_STATUSES`, `PLACEHOLDER_TOKENS`, `_placeholder_token`, post-draft invariant logic in `validate_file`. Threads `RefIndex` through `validate_file` (since `aafa88d04`).
- `plugins/a4/scripts/markdown_validator/registry.py` — three checks registered (`frontmatter`, `status`, `transitions`).
- `plugins/a4/scripts/markdown.py` — adds `extract_preamble_from_text(text)` for parsing `git show` stdout.
- `plugins/a4/scripts/a4_hook.py` — Stop subcommand now runs both `frontmatter` and `transitions` validators against session-edited files; rc=2 on either category's violations.
- `plugins/a4/scripts/transition_status.py` — happy-path writer; `_cascade_*` and `transition()` / `--validate` / `sweep()` all import cascade data + predicates from `status_model`. Length 1011 lines; refactor candidates noted in **Open Questions**.
- `plugins/a4/references/frontmatter-schema.md` — schema enforcement table now lists `unresolved-ref`, `id-filename-mismatch`, `missing-actors-post-draft`, `placeholder-in-title`, `illegal-transition`. §"Status writers" describes the writer + safety-net split. §"Cross-references" → "Status model (canonical)" enumerates the new constants and predicates.
- `plugins/a4/references/body-conventions.md` — body link section notes plain `#<id>` text is acceptable in prose for GitHub-Issues mirroring.
- `plugins/a4/hooks/hooks.json` — top-level description updated to mention the Stop transition-legality safety net.
- `.claude-plugin/marketplace.json` — a4 plugin at `9.5.1`.

## Related Links

- Previous handoff (parent thread queue): `.handoff/3-2026-04-29_2250-markdown-headings-shipped-frontmatter-split-next.md`. That handoff queued frontmatter-schema decomposition + several small refactors; the earlier-arc commits in this session drained that queue. The validator-hardening work is independent of it.
- a4 plugin contributor notes: `plugins/a4/CLAUDE.md` (directory roles, required reading per change kind, conventions).
- Project-root contract: `CLAUDE.md` — calls out `frontmatter-schema.md` as the binding source for any a4 frontmatter change.
- No external GitHub issues / PRs; everything in-tree.

## Decisions and Rationale

- **Keep `transition_status.py`; do not delete it.** User initially considered removing it on the premise that LLMs handle direct `status:` edits well and cascades are rare. After review, the writer earns its keep on three grounds: (1) atomic `(status, updated)` rewrite avoids the most common LLM forgetting-to-bump-`updated:` mistake, (2) trans­action­al multi-file cascade in one invocation (the LLM doing it via several Edits would create intermediate states the consistency checker flags, lengthening Stop-hook retry loops), (3) `--sweep` recovery for missed supersedes is concise. Instead of deletion, added the transition-legality hook as a safety net for direct edits that bypass the writer. Cascade still must run through `transition_status.py` — the hook only catches the legality dimension.
- **transition-legality safety net is git-diff-based, not state-based.** `markdown_validator/transitions.py` reads HEAD via `git show HEAD:<rel>` and compares against the working tree. New files in the working tree are skipped (no baseline; the schema's static checks own initial-status validation). Idea / spark families are absent from `FAMILY_TRANSITIONS` and skipped — they are user-driven.
- **`status_model.py` is the single canonical home for status semantics.** Cascade input/output sets and supersedes-trigger maps lived inline in three modules (`transition_status.py`, `status_consistency.py`, `transitions.py`). Centralizing into `status_model.py` keeps the writer and the consistency-check safety net in lockstep — change one fact, all consumers follow. Predicates (`is_transition_legal`, `legal_targets_from`, `is_terminal`) absorb four duplicated `FAMILY_TRANSITIONS.get(...).get(...)` lookups.
- **Data vs IO vs behavior split:** status_model holds pure constants + predicates only. Path classification (`detect_type` / `_check_one` folder logic) stays in `common.py` / `frontmatter.py` / `transitions.py`. Frontmatter parsing stays in `markdown.py`. Cascade behavior (target discovery + write) stays in `transition_status.py`.
- **Topic change**: this session pivoted from `a4-xml-body-format` (frontmatter schema split, body conventions) to validator hardening starting at `af0c891f7`. New topic `a4-validator-hardening` registers the pivot. `previous:` still references the prior handoff so the chain is preserved.
- **Marketplace bump policy**: feature additions get minor bumps (e.g., `9.5.0` for transitions safety net); pure refactors get patch bumps (`9.5.1` for status_model centralization).
- **Unresolved review-target list bug surfaced but not fixed in this session.** `transition_status.find_reviews_targeting` only handles `target:` as a string scalar, but the schema defines it as a list. Discovered during smoke tests of the discard cascade. The static `status_consistency.check_discarded_cascade` correctly handles list targets and flags the drift, so the workflow degrades gracefully (cascade misses → drift surfaced as `missing-discarded-status-review`). Fix deferred — see Next Steps.

## Important Dialog

- "transition_status.py 놔두는게 좋은가." → "놔두는 쪽 추천" (with three reasons: atomicity, `updated:` co-write, `--sweep`). User: "safety net으로 hook 추가." → led to `markdown_validator/transitions.py` and the Stop-hook integration.
- "status_model.py 도 있네" → user pointing out the canonical module; answered with a structured proposal moving `SUPERSEDES_FAMILIES` (rename to `SUPERSEDES_TRIGGER_STATUS`), `SUPERSEDABLE_FROM_STATUSES`, `TASK_RESET_*`, `REVIEW_TERMINAL`, and the three predicates into `status_model`. User: "묶어서 진행." → executed as commit `276c216c2`.
- Hard requirement (carries forward): "[[wikilink]]는 하위 호환도 안하는 걸로" — no compat shim for the old convention; the frontmatter validator's `[[` reject still serves as a backsliding guard.
- Project rule (always-on): "When making function calls using tools that accept array or object parameters ensure those are structured using JSON" (system).
- Korean honorific (존댓말) is the active mode for chat replies; file content stays in English.

## Validation

All commands run from repo root unless noted. Outputs verbatim where short.

- `git status --short` → empty (clean working tree).
- `git log -1 --oneline` → `276c216c2 refactor(a4): centralize cascade-target data and legality predicates in status_model`.
- `uv run --with pyyaml plugins/a4/scripts/validate.py --list-checks`:
  ```
  frontmatter [workspace+file] — YAML schema (required fields, enums, types), path-reference format, wiki `type:` matches filename, id uniqueness.
  status [workspace+file] — Cross-file status consistency — `supersedes` ↔ status, `promoted` ↔ status, UC discard cascades to task / review.
  transitions [workspace+file] — Status transition legality — diff working tree against HEAD via git and reject `status:` jumps not allowed by the family transition table. Safety net for hand edits that bypass `transition_status.py`.
  ```
- Import sanity (predicates resolve correctly):
  ```
  is_transition_legal('usecase', 'draft', 'ready')   = True
  is_transition_legal('usecase', 'draft', 'shipped') = False
  SUPERSEDES_TRIGGER_STATUS = {'spec': 'active', 'usecase': 'shipped'}
  ```
- `transition_status.py` cascade smoke tests (post `276c216c2` refactor) — see commit message and the conversation transcript:
  - UC `implementing → revising`: both implementing tasks reset `progress`/`failing` → `pending`. Pass.
  - UC `implementing → discarded`: tasks both flip to `discarded`. Pass. Reviews with list-form `target:` are NOT flipped (existing limitation; consistency check catches the drift).
  - spec `draft → active`: prior `spec/1-old.md` correctly cascades `active → superseded`. Pass.
  - illegal spec `active → draft`: rejected with rc=2 and clear "Allowed from `active`: ['deprecated', 'superseded']". Pass.
  - `--validate` mode for spec `active → deprecated`: rc=0, "OK — transition is legal and validations pass." Pass.
- `markdown_validator.transitions` smoke test (earlier in session): legal jumps pass, illegal jumps emit `illegal-transition` violations, idea family and new files (no HEAD baseline) skipped. Pass.
- No language linter run (Python type-checking is not part of this repo's CI; behavior tests cover the change).

## Known Issues and Risks

- **`transition_status.find_reviews_targeting` ignores list-form `target:`.** Affects only the UC-discarded cascade for reviews. The static `check_discarded_cascade` flags the drift, so users see `missing-discarded-status-review` and can fix manually. Pre-existing bug independent of this session's refactor; surfaced during smoke testing.
- `transition_status.py` is 1011 lines and contains four near-identical cascade functions (`_cascade_uc_revising`, `_cascade_uc_discarded`, `_cascade_uc_shipped`, `_cascade_spec_active`). The discussion identified ~270 lines that could collapse into a single cascade engine plus a supersedes-chain primitive. Not done in this session.
- `validate_transition` and `_validate_revising_to_ready` / `_validate_draft_to_active` in `transition_status.py` (~70 lines + the `--force` flag) duplicate the post-draft invariants now enforced statically by `frontmatter.py`. Identified but not removed in this session.
- `_parse(path)` 3-tuple adapter in `transition_status.py` is legacy. Could be inlined to direct `markdown.parse(path)` access.
- `find_tasks_implementing` / `find_reviews_targeting` / `find_usecases_superseded_by` in `transition_status.py` repeat an `iter_issue_files` + `_parse` + filter pattern; could share `collect_family` (currently in `status_consistency.py`).
- `extract_section.py` was deleted as dead code; verified before removal but worth re-checking if anything in user workspaces still references it.
- Stop hook builds a `RefIndex` plus runs the `transitions` git diff for every session-edited file. Cost is bounded by the edited list, but on very large workspaces the full-workspace `--only transitions` CLI mode walks every issue file (no incremental shortcut).
- The transitions safety net relies on `git show HEAD:<rel>` succeeding. If `HEAD` is unborn (fresh repo with no commits) or git is unavailable, the validator silently returns no violations. Documented in the module docstring; do not surprise.

## Next Steps

In priority order. Each is a clean separate commit / PR.

1. **Fix `find_reviews_targeting` to handle list-form `target:`.** Mirror the dual-shape handling already in `status_consistency.check_discarded_cascade`. Small, high-value: removes the only known correctness gap in the UC-discard cascade. Add a smoke test in `transition_status` that exercises a review with list-form target.
2. **Remove duplicated post-draft validation from `transition_status.py`.** Drop `validate_transition`, `_validate_revising_to_ready`, `_validate_draft_to_active`, `PLACEHOLDER_TOKENS`, `_placeholder_in`, `_is_non_empty_list`, the `--force` flag, and the `validation_issues` field on `Report`. Audit skills / agents for `--force` use first (none expected — the `frontmatter` validator now blocks at Stop). ~70 line reduction.
3. **Consolidate the four `_cascade_*` functions into a single cascade engine.** Two primitives:
   - `_apply_cascade(targets, expected_from: frozenset, to: str, reason_fn, report)` for UC revising / UC discarded (task) / UC discarded (review).
   - `_apply_supersedes_chain(family, ref, report)` for UC shipped / spec active. Reads `SUPERSEDES_TRIGGER_STATUS` and `SUPERSEDABLE_FROM_STATUSES` from `status_model`.
   Verify behavior identity by re-running the cascade smoke tests in this handoff. ~150–170 line reduction.
4. **Sharpen `--dry-run` semantics in `transition_status._apply_status_change`.** Currently dry-run short-circuits before parsing/validating, so dry-run misses errors a real run would surface. Move the gate to right before `path.write_text` so dry-run becomes a true preview.
5. **Lift `collect_family(a4_dir, family)` and `read_fm(path)` to shared layers.** `collect_family` to `common.py` (or `markdown_validator/refs.py`); `read_fm` to `markdown.py`. Then rewrite `find_tasks_implementing` / `find_reviews_targeting` / `find_usecases_superseded_by` against `collect_family`. Modest gain.
6. **Decide on `task.files:` artifact-path enforcement** (item 4 in `frontmatter-schema.md` §"Known deferred items"). Per-kind prefix + id-vs-path consistency. Static check, fits naturally next to existing path-format validation.
7. **`research` `complete` initial-status preflight** (deferred item 5). Path existence on `files:` for `kind: research` at `status: complete`.

The first three items are the natural follow-on for this thread; #1 should land before any further refactor of `transition_status.py` so the cascade-engine refactor in #3 inherits the bug fix.

## Open Questions

- Should `--force` be removed entirely, or kept for emergency bypass once the duplicate validation is dropped? Argument for removal: with static post-draft invariants in `frontmatter.py`, the only thing `--force` could bypass is the legality table itself, which would defeat the writer's purpose. Tentative answer: drop it. Confirm before doing #2 above.
- Cascade engine in #3 — should the data table for "what cascades for which transition" live in `status_model.py` (`CASCADE_TRIGGERS_BY_FAMILY`) or stay implicit in dispatch logic in `transition_status.transition()`? Argument for promoting it: gives `markdown_validator.status_consistency` a way to derive expected cascades from the same table the writer uses. Argument against: half-data half-behavior, may force unhelpful abstraction.
- The transitions hook reports per-file but has no aggregation mode. Should `validate.py --only transitions` prefer per-file diff-since-HEAD output rather than the workspace sweep? Current sweep walks every issue file; a `--since HEAD` mode would mirror what pre-commit hooks expect.

## Useful Commands and Outputs

```sh
# Inspect this session's commits since the previous handoff
git log ea4ada2a1..HEAD --oneline

# Exact diffs for the validator-hardening arc
git show af0c891f7    # id-filename-mismatch on stop hook
git show 33bbe13a9    # check_revising_cascade
git show adf947e98    # post-draft authoring invariants
git show 6e8291ac2    # transition-legality safety net (new transitions.py + hook wiring)
git show 276c216c2    # status_model centralization

# Run all checks against a workspace
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir>

# Run only the transitions safety net (workspace sweep)
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir> --only transitions

# Validate a single file's frontmatter (file-scoped path-existence checking still builds workspace RefIndex internally)
uv run --with pyyaml plugins/a4/scripts/validate.py <a4-dir> <file> --only frontmatter

# Happy-path writer (still the recommended interface)
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --to <status> --reason "..."
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --file <path> --validate --to <status>
uv run --with pyyaml plugins/a4/scripts/transition_status.py <a4-dir> --sweep
```

To reproduce the cascade smoke tests, see the conversation transcript before this handoff or recreate via:

```sh
tmpdir=$(mktemp -d); cd "$tmpdir" && git init -q
mkdir -p a4/usecase a4/task/feature a4/review a4/spec
# author UC at 'implementing' + tasks at 'progress'/'failing' + a review with list-target → commit
# then run `transition_status.py --file usecase/<...>.md --to revising` and inspect the cascade report
```

The conversation history before this handoff has the full inline scripts.
