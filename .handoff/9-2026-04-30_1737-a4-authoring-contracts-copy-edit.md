---
sequence: 9
timestamp: 2026-04-30_1737
timezone: KST +0900
topic: a4-v12-refactor
previous: 8-2026-04-30_1728-a4-v12-task-family-split-and-rename.md
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_1737. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Pick up follow-up #3 from handoff 8 — copy-edit the four issue-family authoring contracts (`task-authoring.md`, `bug-authoring.md`, `spike-authoring.md`, `research-authoring.md`) for awkward phrasings introduced by the v12.0.0 split + v12.1.0 rename substring substitutions. No structural / schema changes; pure prose cleanup.

This session began with the user opening `.handoff/8-2026-04-30_1728-a4-v12-task-family-split-and-rename.md` (autoloaded into context) and choosing item 3 from its "Next Steps" list ("Copy-edit the four authoring contracts for awkward phrasings that came from substring substitution"). Topic carried over from handoff 8.

## Current State

- **Branch:** `main`, working tree clean. 73 commits ahead of `origin/main` (handoff 8 reported 72; this session added 1 prose-only commit).
- **Latest two commits (this session):**
  - `1a9b13ec5` — `docs(a4): copy-edit authoring contracts after v12.1.0 rename`
  - `8754693e7` — `docs(handoff): snapshot a4-v12-refactor session state` (handoff 8, prior session)
- **Plugin version:** a4 = `12.1.0` in `.claude-plugin/marketplace.json` — unchanged this session (prose-only commit, no version bump).
- **Schema / structural state:** unchanged from handoff 8. Issue families `usecase`, `task`, `bug`, `spike`, `research`, `review`, `spec`, `idea`. Validator, status writer, scripts untouched.

## Changes Made

### Copy-edit pass (commit `1a9b13ec5`)

Single coherent prose-only commit touching only the four issue-family authoring contracts under `plugins/a4/references/`. 4 files changed, 21+/21−. No imports, no schema, no validator, no scripts touched.

Edits per file (exact lines available via `git show 1a9b13ec5`):

- **`task-authoring.md`** — "the four **task** issue families" → "the four issue families" (matched the wording used by the other three sibling files).

- **`bug-authoring.md`**
  - Title: `# a4 — bug task authoring` → `# a4 — bug authoring` (the leading-paragraph "A bug task at..." also dropped the redundant "task" — now "A bug at...").
  - `## Common mistakes (bug-task-specific)` → `(bug-specific)`.
  - `## Don't (bug-task-specific)` → `(bug-specific)`.
  - Section header `Writer rules (task-specific):` → `Writer rules (bug-specific):` (the "task-specific" wording was a leftover from the v11 era where all four families lived under `a4/task/<kind>/`; post-rename it reads ambiguously since `task` is now a member name).

- **`spike-authoring.md`**
  - Title: `# a4 — spike task authoring` → `# a4 — spike authoring` (leading paragraph "A spike task at..." → "A spike at...").
  - `(spike-task-specific)` → `(spike-specific)` x2.
  - `Writer rules (task-specific):` → `Writer rules (spike-specific):`.
  - Two literal-repetition fixes from substring substitution: ``a `task` task`` → ``a `type: task``` (in two places — the `implements:`-forbidden bullet and the matching "Don't" bullet).
  - **Leftover v11 reference fix**: ``follow up with a `feature` task`` → ``follow up with a `task` (the default issue family)``. This was a stale `feature`-era pointer that survived the v12.1.0 sed pass (handoff 8's straggler scan grep didn't catch it because the surrounding context was pure prose, not one of the renamed paths/skill names).
  - "reserved for `` `task` and `bug` tasks ``" → "reserved for `type: task` and `type: bug`" (cleaner since `task` is now both the umbrella reading and a member type).

- **`research-authoring.md`**
  - Title: `# a4 — research task authoring` → `# a4 — research authoring` (leading paragraph "A research task at..." → "A research item at..." — picked "item" over "entry" / "task" because "research task" reads ambiguously now).
  - `Writer rules (task-specific):` → `Writer rules (research-specific):`.
  - `## Don't (research-task-specific)` → `(research-specific)`.
  - **Second leftover v11 reference fix**: `## Citing a research task from a spec or feature` → `## Citing a research task from a spec or task` (same class as the spike fix; the substring substitution missed this because the v12.1.0 sed targeted file paths and skill names, not bare prose mentions of `feature`).
  - "reserved for `` `task` and `bug` tasks ``" → "reserved for `type: task` and `type: bug`".

### Out of scope (intentionally)

- Validator rule names retaining `task-` prefix (`task-artifacts-bad-path`, `task-artifacts-missing-file`) — handoff 8 #4 in Known Issues. Cosmetic-only and intentionally deferred there to avoid breaking downstream rule-id consumers.
- `TASK_TRANSITIONS` constant in `status_model.py` — handoff 8 next-step #4. Pure cosmetic rename, not pursued this session.
- Plugin-validator re-run after v12.1.0 — handoff 8 next-step #1. Not pursued (this session's edits are prose-only and don't affect any validator-checked surface).

## Key Files

| Path | Why it matters |
|------|----------------|
| `plugins/a4/references/task-authoring.md` | Default-family authoring contract — `type: task` (renamed from `feature` in v12.1.0). |
| `plugins/a4/references/bug-authoring.md` | `type: bug` authoring contract. |
| `plugins/a4/references/spike-authoring.md` | `type: spike` authoring contract. Largest delta this session (8 lines) due to two `feature`-era references that survived v12.1.0. |
| `plugins/a4/references/research-authoring.md` | `type: research` authoring contract. Second-largest delta (6 lines). |
| `.handoff/8-2026-04-30_1728-a4-v12-task-family-split-and-rename.md` | Prior handoff this session continued. Read first if more v12-refactor work needs to be picked up — it carries the full Decisions-and-Rationale chain plus the remaining next-step queue. |

## Related Links

No GitHub issues, PRs, or wiki pages — this was a single-session prose cleanup landing as a direct commit on `main`. Continuation context lives entirely in handoff 8 and the two v12 commits it points at (`e417391e7` v12.0.0, `61ce608de` v12.1.0).

## Decisions and Rationale

1. **Title pattern: drop the "task" word from non-`task` family titles.** Originally all four files used `# a4 — <type> task authoring`. After v12.1.0 made `task` a specific member name (not just an umbrella), `# a4 — research task authoring` reads as either "research-typed task authoring" or "authoring of research tasks" — both awkward. Dropping the redundant "task" matches the `task-authoring.md` title which never had it. The leading paragraph followed (`A bug task at...` → `A bug at...`, etc.) for consistency.

2. **`Writer rules (task-specific):` → per-family.** Originally a generic "rules specific to issue-family items (vs. universal across all artifacts)" header — the `task-` prefix meant "the task issue family" in the v11 sense. Post-rename, "task-specific" suggests rules specific to `type: task` only, which is wrong. Per-family naming (`bug-specific` / `spike-specific` / `research-specific`) is unambiguous and cheap.

3. **Why `a `type: task`` instead of `a `task` task` or `a regular `task``.** The earlier draft considered `regular task` to disambiguate. Settled on `type: task` because (a) it's the unambiguous frontmatter literal, (b) it parallels existing prose patterns elsewhere in the same files (`type: spike`, `type: bug`), and (c) "regular" introduces a vague qualifier the rest of the docs don't use.

4. **Why "research **item**" not "research task" in the leading paragraph.** Same kind of ambiguity as the title issue. "Item" is a generic placeholder that doesn't conflict with the `task` member-name reading. Used only in the leading paragraph; the rest of the file still says "research task" where context makes the meaning clear (e.g., "Citing a research task from a spec or task" — here the pairing with "spec" makes the `type: research` reading obvious).

5. **Two `feature`-era leftovers were genuinely missed by handoff 8's straggler scan.** Handoff 8 reported a clean grep for `feature-authoring|/a4:feature|skills/feature/|a4/feature/|TASK_FAMILY_TYPES`. Both fixes this session — `spike-authoring.md` "follow up with a `feature` task" and `research-authoring.md` "spec or feature" — were prose-level mentions of the bare word `feature` that the path/identifier-targeted scan deliberately did not catch. This was expected behavior of the scan, but worth noting for future renames: bare-word prose mentions need a separate, broader pass (`grep -nw feature`) when a member-type rename happens.

6. **Single commit, not four.** All edits are the same kind (prose cleanup of v12.1.0 substitution leftovers in a single reference family). Splitting per-file would produce four commits with near-identical messages and no review value. Handoff 8 set the precedent of one commit per coherent slice; one slice → one commit.

## Important Dialog

- User picked the work with a single character: `3`. That mapped to the third bullet of handoff 8's "Next Steps" list ("Copy-edit the four authoring contracts… for awkward phrasings that came from substring substitution"). Auto Mode active throughout, so I executed without further confirmation per the in-effect harness instructions.
- No mid-session course-corrections from the user. The session's only signal was the initial `3` plus the wrap-up `/handoff` invocation.

## Validation

| Check | Command | Result |
|-------|---------|--------|
| Awkward-phrasing scan (in-file) | `grep -nE "task task\|feature task\|task-task\|four task issue\|and \`bug\` tasks\|task-task-specific" plugins/a4/references/{task,bug,spike,research}-authoring.md` | **PASS** — empty output. |
| Bare `feature` scan in 4 files | `grep -n "feature" plugins/a4/references/{task,bug,spike,research}-authoring.md` | **PASS** — empty output. |
| Repo-wide v12 path/identifier straggler | `git ls-files \| xargs grep -l "feature-authoring\|/a4:feature\|skills/feature/\|a4/feature/\|TASK_FAMILY_TYPES" 2>/dev/null` | Two hits, both in `.handoff/` (`3-2026-04-29_2250-…md` and `8-2026-04-30_1728-…md`). Both are point-in-time handoff snapshots that must not be edited. **No hits in `plugins/a4` or `.claude-plugin`.** |
| Plugin-validator | (not run) | **Skipped** — edits are prose-only inside `references/*.md` files that the plugin-validator agent treats as documentation. Handoff 8 carried plugin-validator as next-step #1 (still outstanding) and the right pass for that is a fresh top-of-tree run, not a delta on this commit. |
| Frontmatter / status / transitions / cascade | (not run) | **Skipped** — no schema or script files were touched this session; the handoff-8 e2e fixture run is still authoritative for the runtime surface. |

## Known Issues and Risks

1. **Plugin-validator still not re-run since v12.0.0.** Carried forward from handoff 8 #1. This session's edits are prose-only and don't change the assessment — but the bullet remains a true outstanding follow-up.
2. **No automated migration tool for v11 → v12.x.** Carried forward from handoff 8 #2. This session does not affect end-user migration steps.
3. **`TASK_TRANSITIONS`, validator rule-id `task-` prefixes** — carried forward from handoff 8 #4 / #5. Both unchanged.
4. **Some prose still says "research task" / "bug task" where the meaning is generic ("an item of type X").** Most of those are fine in context — e.g., "closed bug tasks archive their markdown" reads naturally. They were left alone deliberately. If the dual-meaning of `task` does become a real reader-confusion point, a broader rewrite to "bug item" / "research item" / "spike item" would be the next step (handoff 8 open-question #3).
5. **README / CLAUDE.md not touched.** Handoff 8 #6 noted some pre-v12 example paths may persist in those longer documents. This session focused only on the four authoring contracts; README/CLAUDE.md remain on the same straggler-scan-clean baseline as handoff 8.

## Next Steps

In rough priority order, pulling forward from handoff 8 with this session's progress applied:

1. **Re-run `plugin-dev:plugin-validator`** to confirm v12.1.0 + this prose pass land clean. Top remaining follow-up — unchanged in priority from handoff 8.
2. **Add an upgrade-notes section to plugin README** covering v11 → v12.1 manual migration. Same as handoff 8 #2.
3. **Consider renaming `TASK_TRANSITIONS`** in `status_model.py` for symmetry with `ISSUE_FAMILY_TYPES`. Cosmetic. Same as handoff 8 #4.
4. **Optional: rename validator rule ids** `task-artifacts-bad-path` etc. for consistency with renamed `references/artifacts.md`. Same as handoff 8 #5.
5. **Optional: broader copy-edit pass over the longer plugin docs** (`plugins/a4/README.md`, `plugins/a4/CLAUDE.md`, `plugins/a4/docs/*.md`) for `feature`-era bare prose that the path-targeted v12.1.0 scan would have missed. This session caught two such cases inside the four authoring contracts; the longer docs may have similar leftovers.
6. **Push to `origin/main`** when the user is ready. Currently 73 commits ahead.

## Open Questions

Carried forward from handoff 8 unchanged (none of them advanced this session):

1. Should there be a single top-level `references/upgrade-notes.md` consolidating v6 → v12.1.0 hand-migration?
2. Should `workspace_state.py` get a "task issue families" header above the per-family rows in `render_issue_counts`?
3. Is the `task` dual-meaning (umbrella vs. member) actually causing reader confusion in practice?

## Useful Commands and Outputs

```bash
# This session's commits
git log --oneline -3
#   1a9b13ec5 docs(a4): copy-edit authoring contracts after v12.1.0 rename
#   8754693e7 docs(handoff): snapshot a4-v12-refactor session state
#   61ce608de refactor(a4)!: rename `feature` issue family to `task` (v12.1.0)

# Inspect this session's prose-only diff
git show 1a9b13ec5
git show --stat 1a9b13ec5
# Expected: 4 files, 21+/21- under plugins/a4/references/

# Re-run the awkward-phrasing scan (should stay empty)
grep -nE "task task|feature task|task-task|four task issue|and \`bug\` tasks|task-task-specific" \
  plugins/a4/references/task-authoring.md \
  plugins/a4/references/bug-authoring.md \
  plugins/a4/references/spike-authoring.md \
  plugins/a4/references/research-authoring.md

# Re-run the bare `feature` scan inside the four authoring files
grep -n "feature" \
  plugins/a4/references/task-authoring.md \
  plugins/a4/references/bug-authoring.md \
  plugins/a4/references/spike-authoring.md \
  plugins/a4/references/research-authoring.md

# Repo-wide v12 path/identifier straggler scan (handoff 8's command, still useful)
git ls-files | xargs grep -l "feature-authoring\|/a4:feature\|skills/feature/\|a4/feature/\|TASK_FAMILY_TYPES" 2>/dev/null
# Hits should appear only under .handoff/ (point-in-time snapshots, do not edit).

# Pick up the top remaining follow-up
# Invoke `plugin-dev:plugin-validator` agent on /Users/myungo/GitHub/studykit-plugins/plugins/a4
```
