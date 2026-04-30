---
sequence: 8
timestamp: 2026-04-30_1728
timezone: KST +0900
topic: a4-v12-refactor
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1728. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Split the previous combined `a4/task/` issue folder (with a `kind:` discriminator) into four flat sibling top-level folders, each with its own `type:` literal and authoring contract. After deciding the split was the right shape, simplify the default kind's name from `feature` back to `task` (matching Jira's "Task" issue type alongside Bug / Spike / Research). Land both changes as separate breaking releases of the a4 plugin.

This session was driven entirely by `/clear` then a fresh design conversation; it did not start from a specific prior handoff. Topic chosen as `a4-v12-refactor` because the focus is the v12 family-split refactor, distinct from prior `a4-validator-hardening` work captured in handoffs 4–7.

## Current State

- **Branch:** `main`, ahead of `origin/main` by 72 commits (this session added 2). Working tree clean.
- **Latest two commits (this session):**
  - `61ce608de` — `refactor(a4)!: rename feature issue family to task (v12.1.0)`
  - `e417391e7` — `feat(a4)!: split task family into per-type folders + skills (v12.0.0)`
- **Plugin version:** a4 = `12.1.0` in `.claude-plugin/marketplace.json`.
- **Issue families (after both commits):** `usecase`, `task`, `bug`, `spike`, `research`, `review`, `spec`, `idea`. The four task issue families share `TASK_TRANSITIONS` and the `_TASK_STATUSES` / `_TASK_TERMINAL` / `_TASK_IN_PROGRESS` enums in `status_model.py`.
- **Cross-family grouping constant:** `status_model.ISSUE_FAMILY_TYPES = ("task", "bug", "spike", "research")`. The earlier name `TASK_FAMILY_TYPES` from v12.0.0 was renamed to `ISSUE_FAMILY_TYPES` in v12.1.0 to disambiguate "issue family" (the four-folder grouping) from the specific `type: task` family.
- **Skills:** `/a4:task` (default issue family), `/a4:bug`, `/a4:spike`, `/a4:research`, `/a4:discard`. The v11 umbrella `/a4:task kind=…` skill was retired in v12.0.0; the new `/a4:task` (added v12.1.0) writes only the default-kind family.
- **References renamed:** `references/feature-authoring.md` → `task-authoring.md`. `references/task-artifacts.md` → `artifacts.md`. Same shape applied to `rules/a4-feature-authoring.md` → `a4-task-authoring.md`. Three other family rules (`a4-bug-authoring.md`, `a4-spike-authoring.md`, `a4-research-authoring.md`) already existed from v12.0.0.

## Changes Made

### v12.0.0 — task family split (commit `e417391e7`)

Promote the four task kinds (feature/bug/spike/research) from `a4/task/<kind>/` subfolders with a `kind:` discriminator to flat sibling top-level folders, each with its own `type:` literal and authoring contract. Retired the `task` umbrella concept across schema, validators, status writer, references, rules, skills, agents, docs, and scripts. 79 files changed (1360+/797−).

Highlights:

- Frontmatter `type:` values: `task` → one of `feature` / `bug` / `spike` / `research`; `kind:` field on tasks removed.
- Path layout: `a4/task/<kind>/<id>-<slug>.md` → `a4/<type>/<id>-<slug>.md`.
- Path-ref form: `task/<id>-<slug>` → `<type>/<id>-<slug>` (bare integer short form unchanged).
- Artifact directory prefix: `artifacts/task/<kind>/...` → `artifacts/<type>/...` (spike archive: `artifacts/spike/archive/...`).
- Validation rule `kind-field-forbidden` → `type-field-forbidden`. spike/research schemas explicitly forbid `implements:` / `spec:` / `cycle:`. research adds required `mode:` (comparative | single) and conditional `options:`.
- Skills: `/a4:task` (umbrella, removed). New entry points `/a4:feature`, `/a4:bug`, `/a4:spike`, `/a4:research`, `/a4:discard`.
- References renamed: `task-{feature,bug,spike,research}-authoring.md` → `{feature,bug,spike,research}-authoring.md`; `task-artifacts.md` → `artifacts.md`. Path-scoped rules under `rules/` likewise renamed.
- Marketplace bumped to `12.0.0`.
- Plugin-validator (`plugin-dev:plugin-validator`) ran clean PASS at the end of v12.0.0.

For exact file changes: `git show e417391e7` and `git diff e060269dd..e417391e7`.

### v12.1.0 — feature → task rename (commit `61ce608de`)

Rename the default task issue family from `feature` to `task`, matching Jira's "Task" issue type that sits alongside Bug / Story / Epic. Retire "task family" umbrella terminology in favor of "issue family" to disambiguate the family-level concept from the specific `type: task` member. 59 files changed (339+/328−).

Highlights:

- Frontmatter `type:` value `feature` → `task`.
- Folder layout: `a4/feature/` → `a4/task/`.
- Path-ref form: `feature/<id>[-<slug>]` → `task/<id>[-<slug>]`.
- Artifact directory prefix: `artifacts/feature/...` → `artifacts/task/...`.
- Skill name: `/a4:feature` → `/a4:task` (writes default-kind family; not the same as v11's umbrella `/a4:task`).
- Constant rename: `status_model.TASK_FAMILY_TYPES` → `ISSUE_FAMILY_TYPES`.
- References / rules renamed: `feature-authoring.md` → `task-authoring.md`; `a4-feature-authoring.md` → `a4-task-authoring.md`. Path-scoped rule glob retargeted to `a4/task/**/*.md`.
- Skill folder renamed: `skills/feature/` → `skills/task/`.
- Marketplace bumped to `12.1.0`.

For exact file changes: `git show 61ce608de`.

### Process notes

- Split work into 8 phases (P1–P8) and tracked via TaskCreate/TaskUpdate. Same shape repeated for the v12.1.0 rename (R1–R6).
- Validation gates after each phase: import sanity check via `uv run --with pyyaml python -c "import status_model, common, ..."` from `plugins/a4/`. Then a 5-file fixture under `/tmp/a4test*` exercising `validate.py` (frontmatter / status / transitions all OK) and `transition_status.py --dry-run` for UC `→ revising` cascade across two families.
- A linter / hook touched several files mid-edit (the auto-loaded a4-section-enum / authoring rules), surfacing as the editor's "File has been modified since read" error a few times. Re-reading and re-editing resolved each occurrence.
- Sed-based bulk substitutions used for `feature` → `task` in skills/, agents/, docs/. Followed by Python-based pass for harder phrases ("four task families", "feature task body", etc.). Each pass followed by a `grep -rnE …` straggler scan.
- Plugin-validator PASS achieved at end of v12.0.0; not re-run for v12.1.0 (verified via the e2e fixture instead).

## Key Files

| Path | Why it matters |
|------|----------------|
| `plugins/a4/scripts/status_model.py` | Single source of truth for issue family enums, transitions, terminal/in-progress sets, `ISSUE_FAMILY_TYPES` grouping, `KIND_BY_FOLDER` (review only). All other scripts import from here. |
| `plugins/a4/scripts/common.py` | `ISSUE_FOLDERS` tuple (drives validator/writer iteration). Flat layout — no nested-folder helpers anymore. |
| `plugins/a4/scripts/markdown_validator/frontmatter.py` | Per-type schemas (10 entries: wiki, usecase, task, bug, spike, research, review, spec, idea, spark_brainstorm). `forbidden_fields` mechanism on spike/research to enforce no-implements/no-spec/no-cycle as a structural rule. |
| `plugins/a4/scripts/transition_status.py` | Status writer + cascade engine. `find_tasks_implementing` walks `ISSUE_FAMILY_TYPES`. Cascade row labels derived from `path.parent.name` (the family folder). |
| `plugins/a4/scripts/markdown_validator/status_consistency.py` | Cascade-drift detector. Loops over `ISSUE_FAMILY_TYPES` for both UC-discarded and UC-revising drift checks, emitting per-family rule names (e.g., `missing-discarded-status-task`, `missing-discarded-status-bug`, etc.). |
| `plugins/a4/references/frontmatter-schema.md` | Prose schema reference (single source of truth for human readers). Mirrors `status_model.py`. |
| `plugins/a4/references/{task,bug,spike,research}-authoring.md` | Per-family authoring contracts. Each cites `frontmatter-schema.md` and `body-conventions.md`. |
| `plugins/a4/references/artifacts.md` | Cross-family artifact-directory contract: `artifacts/<type>/<id>-<slug>/`, spike archive convention. |
| `plugins/a4/skills/{task,bug,spike,research,discard}/` | Five new (in v12.0.0; renamed in v12.1.0) skills. Each SKILL.md is thin orchestration; `references/author-flow.md` carries the procedure. |
| `plugins/a4/skills/run/SKILL.md` | Implement loop. Reads from all four issue family folders. Mode-detection bash uses `ls a4/task/*.md a4/bug/*.md a4/spike/*.md a4/research/*.md`. |
| `plugins/a4/skills/roadmap/SKILL.md` | UC-batch generator. Always emits `type: task` for the batch path; spike / bug / research come through their dedicated authoring skills. |
| `plugins/a4/agents/task-implementer.md` | Reads task files at `a4/<type>/<id>-<slug>.md`. Commit-message `<type>` → `feat` for `type: task`, `fix` for `bug`, `chore` for `spike`, `docs` for `research`. |
| `plugins/a4/agents/roadmap-reviewer.md` | Walks the four issue family folders. References `[<type>/<id>-<slug>](../<type>/<id>-<slug>.md)` for review-item evidence. |
| `plugins/a4/CLAUDE.md`, `plugins/a4/README.md` | Plugin-developer notes + end-user README updated for the new layout. README directory diagram shows the four flat task folders. |
| `.claude-plugin/marketplace.json` | a4 entry version `12.1.0`. |

## Related Links

- **Prior validator-hardening work:** handoffs 4–7 (`.handoff/4..7-*.md`) capture the validator hardening that landed before this refactor. Notable entries: handoff 7 closed out research-preflight skip-label work; handoff 6 finished cascade engine consolidation. Useful when reading the writer/validator code because some structural choices (e.g., shared `_apply_reverse_cascade`, cascade-trigger map) come from that thread.
- **a4 spec rationales (in-workspace):** Several `plugins/a4/spec/archive/2026-04-24-*.md` files document the original task-kind / experiments-slot decisions superseded by the v12 split. README and CLAUDE.md still cite them for historical rationale.

There are no GitHub issues or PRs for this work — it ships as direct commits to `main`.

## Decisions and Rationale

1. **Why split `task` into four folders rather than keep a single `task/` with `kind:`.**
   The user explicitly chose "전면 분리" (full split) after a feasibility review. The split removes conditional schema rules ("kind=spike forbids implements") in favor of structural per-type schemas; reduces SKILL.md if-kind branching; tightens skill triggering by giving each kind its own description / argument-hint; aligns with Jira's per-issue-type model. Cost was acknowledged as ~30 file changes + breaking workspace migration.

2. **Why no migration tool was shipped.**
   User explicit instruction: "migration 도구는 안 만드는 걸로." Existing workspaces upgrade by hand (file moves + frontmatter rewrites). Both commit messages document the manual migration steps.

3. **Why the default kind reverted from `feature` back to `task` in v12.1.0.**
   After landing v12.0.0, the user noticed that `feature` is a4-specific jargon while Jira's universal model is `Task` / `Bug` / `Story` / `Epic`. Reverting the default kind's name to `task` matches that mental model exactly: "Task is both an umbrella term in casual speech and a specific issue type alongside Bug." User accepted the dual meaning explicitly: "이름 이중화: task family를 issue family로", "명령어 충돌 문제 안됨", "clean break. migration 안내 필요 없음."

4. **Why "task family" was renamed to "issue family".**
   With `task` becoming both a member name and (informally) an umbrella, the previous label "task family" became ambiguous. "Issue family" cleanly identifies the cross-family grouping concept (the four sibling folders) without colliding with the specific `type: task` member. Code constant followed: `TASK_FAMILY_TYPES` → `ISSUE_FAMILY_TYPES`.

5. **Why `kind:` field was removed entirely (not retained as redundant metadata).**
   The folder + `type:` literal together encode the kind unambiguously. Carrying a redundant `kind:` field invites drift between the folder and the field. Validator rule `type-field-forbidden` enforces this (replaces the old `kind-field-forbidden`).

6. **Why path-refs use the actual folder (`task/<id>-<slug>`) rather than a kind-segment form (`task/task/<id>-<slug>` or similar).**
   The legacy `task/<kind>/<id>-<slug>` form was retired with the folder split. Path refs now match the on-disk folder layout 1:1, so `RefIndex` resolution stays a simple folder-based lookup. Bare integer short form (`3`) keeps working folder-agnostic.

7. **Why research artifact-existence preflight skips `spike` but covers `task` / `bug` / `research`.**
   Inherited from prior validator hardening (handoff 6/7). `spike` is excluded because at `status: complete` the artifact directory may still live at the original prefix until the user `git mv`s it to `artifacts/spike/archive/<id>-<slug>/` — an existence check would race the archive transition.

8. **Why `find` skill keeps `--kind` accepting `task` / `bug` / `spike` / `research` even though those are folder names, not enum values.**
   Search records' `kind` property (in `search.py`) returns the folder name for the four issue families post-v12. Adding singleton entries `{ "task": frozenset({"task"}), ... }` to the validator's `KIND_BY_FOLDER` map lets `--kind task` filter through naturally without special-casing the search filter.

9. **Why both commits use `feat(a4)!:` / `refactor(a4)!:` (with the `!` breaking marker) rather than just `feat(a4):`.**
   Both ship breaking changes (path layout, `type:` enum, skill names). The `!` follows the project's commit-message convention so downstream tooling and changelogs flag them as major-version-bumping.

## Important Dialog

- User on the v12.0.0 design decisions list: the user accepted all 8 proposed defaults at once with the single instruction "migration 도구는 안 만드는 걸로" — this set a strong norm: the v12 work is a clean-break breaking release with hand migration only.
- User rejected partial / alias designs in favor of full split: "전면분리." (just one word) signaled this when the v11→v12 split was still under design.
- User triggered the v12.1.0 rename with: "feature 대신 사용하면 좋은 이름" → "task 로 해도 되지 않을까?" — confirming the `task`-as-default-kind model.
- User authorized the v12.1.0 design adjustments with: "이름 이중화: task family를 issue family로 / 명령어 충돌 문제 안됨 / clean break. migration 안내 필요 없음. commit 후 진행." — this resolved all three concerns I had raised about the rename.
- Mid-session, the user said "commit" twice (no inline scope) — both times I read it as "commit the work that's currently complete in the working tree" and committed accordingly. That pattern is what produced the two separate commits rather than one squashed commit.

## Validation

All checks pass on a fresh fixture exercising all four issue families plus a usecase that triggers a UC-revising cascade.

| Check | Command | Result |
|-------|---------|--------|
| Import sanity | `uv run --with pyyaml python -c "import status_model, common, transition_status, workspace_state, search, allocate_id, a4_hook, generate_status_diagrams; from markdown_validator import frontmatter, refs, status_consistency, transitions"` (from `plugins/a4/`) | OK |
| Frontmatter validator | `uv run --with pyyaml --directory scripts python validate.py /tmp/a4handoff/a4 --only frontmatter` | OK — no issues |
| Status consistency | `uv run --with pyyaml --directory scripts python validate.py /tmp/a4handoff/a4 --only status` | OK — no issues |
| Transition legality | `uv run --with pyyaml --directory scripts python validate.py /tmp/a4handoff/a4 --only transitions` | OK — no issues |
| Cascade dry-run (UC `implementing → revising`) | `uv run --with pyyaml --directory scripts python transition_status.py /tmp/a4handoff/a4 --file usecase/1-x.md --to revising --dry-run` | Cascade fires correctly: `task/2-impl.md: progress → pending` + `bug/3-fix.md: progress → pending`. Both family folders walked. |
| Plugin-validator (last run, end of v12.0.0) | invoked via `plugin-dev:plugin-validator` agent | PASS (per-section breakdown in agent's report). Not re-run after v12.1.0 — relied on e2e fixture above. |

Repo-wide stragglers scan after v12.1.0:

```
git ls-files | xargs grep -l "feature-authoring\|/a4:feature\|skills/feature/\|a4/feature/\|TASK_FAMILY_TYPES" 2>/dev/null
```

Returns no hits in `plugins/a4` or `.claude-plugin`.

## Known Issues and Risks

1. **Plugin-validator not re-run after v12.1.0.** The agent ran clean at the end of v12.0.0; the v12.1.0 changes are mostly substring renames that the e2e fixture covers, but a fresh `plugin-dev:plugin-validator` run would catch anything the substring substitution missed (e.g., a path that the agent reads but no test exercises). Suggested as the first follow-up if anything seems off.
2. **No automated migration script for existing workspaces.** Anyone with an `a4/` workspace on v11 will need to:
   - Move every `a4/task/<kind>/<id>-*.md` to `a4/<kind>/<id>-*.md` (drop the `<kind>/` segment).
   - In each task file: rewrite `type: task` → `type: <kind>`, then in v12.1.0 step rewrite `feature` → `task` for the default kind.
   - Drop the `kind:` line.
   - Update path refs in frontmatter (`implements`, `depends_on`, `target`, `related`) and body links: `task/<id>-<slug>` → `<kind>/<id>-<slug>`, with `feature` further → `task` in v12.1.0.
   - Move artifact directories: `artifacts/task/<kind>/...` → `artifacts/<kind>/...` (v12.0.0), then `artifacts/feature/...` → `artifacts/task/...` (v12.1.0).
   The two commit messages document this manual sequence; consider adding a top-level upgrade note to README later.
3. **Some long substring substitutions left awkward English.** A few prose passages that previously read "`feature` task" now read "`task` task" (literal word repetition). I rewrote the worst offenders to "regular task" or "default kind" but a couple may remain in research/spike/bug authoring docs. Worth a copy-edit pass.
4. **`task-artifacts-bad-path` / `task-artifacts-missing-file` validator rule names retain the `task-` prefix.** They are stable identifiers in violation reports but inconsistent with the renamed `references/artifacts.md`. Plugin-validator flagged this as cosmetic; left intentionally unchanged to avoid breaking downstream consumers that grep by rule name.
5. **`TASK_TRANSITIONS` constant name in `status_model.py` retains "TASK" prefix** even though the four task issue families now share it. The rename is purely cosmetic (the four-family grouping is `ISSUE_FAMILY_TYPES`; this constant is the shared transition table). Left intentionally to avoid yet another constant rename — but may confuse a reader who expects symmetry.
6. **README / CLAUDE.md prose.** Largely up-to-date but some pre-v12 `task/<kind>/` example paths may persist in places I missed. The straggler scan command in §Validation is reliable for catching them.

## Next Steps

In rough priority order:

1. **Re-run `plugin-dev:plugin-validator`** to confirm v12.1.0 lands clean, just as v12.0.0 was validated.
2. **Add an upgrade-notes section to plugin README** that walks v11 → v12.1 migration in one go (the two commit messages are detailed but not where end users will look). Include the exact `find` / `git mv` / `sed` snippets.
3. **Copy-edit the four authoring contracts** (`task-authoring.md`, `bug-authoring.md`, `spike-authoring.md`, `research-authoring.md`) for awkward phrasings that came from substring substitution. Particularly any `task` task / `feature task` artifacts.
4. **Consider renaming `TASK_TRANSITIONS` → `TASK_FAMILY_TRANSITIONS` or similar** in `status_model.py` — small cleanup that makes the symmetry with `ISSUE_FAMILY_TYPES` explicit. Not pressing.
5. **Optional: rename validator rule ids** (`task-artifacts-bad-path` → `artifacts-bad-path`, etc.) for consistency with the renamed reference. Pure cosmetic; only affects the rule-id strings in violation reports. Defer unless a downstream consumer flags it.
6. **Push to `origin/main`** when the user is ready. Currently 72 commits ahead of `origin/main`.

## Open Questions

1. Should there be a single top-level `references/upgrade-notes.md` (or `MIGRATIONS.md`) that consolidates v6 → v10 → v11 → v12.0.0 → v12.1.0 hand-migration guidance? Today each is buried in its own commit message.
2. Should the workspace dashboard (`workspace_state.py`) get a "task issue families" header above the per-family rows in `render_issue_counts`? Today the four rows just appear under `usecase` with no grouping label. Cosmetic.
3. Is the v12.1.0 dual-meaning of `task` (both umbrella and member) actually causing confusion in practice, or only in theory? If users keep saying "task family" out of habit, the docs may need to repeat the disambiguation more aggressively.

## Useful Commands and Outputs

```bash
# View this session's commits
git log --oneline -3
#   61ce608de refactor(a4)!: rename `feature` issue family to `task` (v12.1.0)
#   e417391e7 feat(a4)!: split task family into per-type folders + skills (v12.0.0)
#   a213a74e6 feat(a4)!: replace #<id> path-ref short form with bare YAML integer

# Inspect exact file changes
git show 61ce608de --stat
git show e417391e7 --stat
git diff a213a74e6..61ce608de -- plugins/a4/scripts/status_model.py

# Foundation sanity check (run from plugins/a4/)
cd plugins/a4
uv run --with pyyaml python -c "
import sys; sys.path.insert(0, 'scripts')
import status_model, common
from markdown_validator import frontmatter
print('ISSUE_FAMILY_TYPES =', status_model.ISSUE_FAMILY_TYPES)
print('ISSUE_FOLDERS =', common.ISSUE_FOLDERS)
print('SCHEMAS =', sorted(frontmatter.SCHEMAS))
"
# Expected:
#   ISSUE_FAMILY_TYPES = ('task', 'bug', 'spike', 'research')
#   ISSUE_FOLDERS = ('usecase', 'task', 'bug', 'spike', 'research', 'review', 'spec', 'idea')
#   SCHEMAS = ['bug', 'idea', 'research', 'review', 'spark_brainstorm', 'spec', 'spike', 'task', 'usecase', 'wiki']

# E2E fixture validate (matches §Validation)
mkdir -p /tmp/a4t/a4/{usecase,task,bug,spike,research}
# … then write fixture files (see commit body for shapes) …
uv run --with pyyaml --directory scripts python validate.py /tmp/a4t/a4
uv run --with pyyaml --directory scripts python transition_status.py /tmp/a4t/a4 \
  --file usecase/1-x.md --to revising --dry-run

# Repo-wide straggler scan
git ls-files | xargs grep -l "feature-authoring\|/a4:feature\|skills/feature/\|a4/feature/\|TASK_FAMILY_TYPES" 2>/dev/null
# Should output nothing.

# Re-run plugin-validator (top suggested follow-up)
# Invoke the `plugin-dev:plugin-validator` agent on /Users/myungo/GitHub/studykit-plugins/plugins/a4
```
