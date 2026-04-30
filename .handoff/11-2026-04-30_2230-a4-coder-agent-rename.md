---
sequence: 11
timestamp: 2026-04-30_2230
timezone: KST +0900
topic: a4-coder-rename
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-30_2230. To record a later state, create a new handoff file via `/handoff` — never edit this one.

## Goal

Rename the a4 implementation subagent from `task-implementer` to `coder`. The user wanted a shorter, role-based name (it codes; it doesn't only "implement tasks"). The rename had to propagate through every skill, agent, authoring contract, and workflow reference, plus the `Agent(subagent_type: "a4:<name>")` invocation shape, without breaking citations.

## Current State

- Branch: `main`. Working tree clean before the handoff commit.
- Two pre-handoff commits landed on top of `2ba53a878 docs(a4): add per-directory CLAUDE.md`:
  - `082a3c829 refactor(a4): rename task-implementer agent to coder`
  - `0fcd2f25c chore(a4): bump version to 15.1.0 for coder rename`
- a4 plugin version: `15.1.0` (was `15.0.0`).
- No prior handoff was opened to start this session — `/clear` reset the context, then the user asked questions about `pipeline-shapes.md` (Minimal vs rules/) and which skills cite `workflows/` before requesting the rename.

## Changes Made

**Agent file rename** — `plugins/a4/agents/task-implementer.md` → `plugins/a4/agents/coder.md` via `git mv`. Frontmatter `name:` field updated to match.

**Procedure file rename** — `plugins/a4/skills/run/references/spawn-implementer.md` → `plugins/a4/skills/run/references/spawn-coder.md` to keep the skill's procedure-file naming aligned with the new agent name. The `Agent(subagent_type: "a4:task-implementer")` literal inside that file became `"a4:coder"`.

**Cross-file token sweep** — Bulk-replaced `task-implementer` → `coder` in 19 active files spanning agents, authoring contracts, workflows, skills, and the README. Also fixed the `run/SKILL.md` step table cell that pointed at the old procedure-file name. `.handoff/2-...` and `.handoff/8-...` reference the old name but were intentionally left alone (point-in-time records).

**Marketplace bump** — `.claude-plugin/marketplace.json` `a4.version` `15.0.0` → `15.1.0`. SemVer minor was the user's call (internal agent rename, but the trigger keyword `'task-implementer'` was also live in `run/SKILL.md`'s description — user-visible surface).

For exact diffs see `git show 082a3c829` (rename + sweep) and `git show 0fcd2f25c` (version bump).

## Key Files

- `plugins/a4/agents/coder.md` — renamed agent file. Body still contains `source: coder` literal in two `## Description` review-item examples (architecture-choice exit and spec-ambiguity exit).
- `plugins/a4/skills/run/references/spawn-coder.md` — renamed procedure file. Holds the `Agent(subagent_type: "a4:coder", isolation: "worktree", ...)` invocation template.
- `plugins/a4/skills/run/SKILL.md` — Step 2 of the loop body table now reads `Spawn coder | references/spawn-coder.md`. Skill `description:` field still includes `'task-implementer'` removed and replaced.
- `.claude-plugin/marketplace.json` — version source of truth (per project CLAUDE.md, `plugin.json` must NOT carry `version`).
- `plugins/a4/workflows/pipeline-shapes.md` — context for the earlier discussion (Minimal shape entry skills); left unchanged.
- `plugins/a4/CLAUDE.md` — audience routing reference.

## Related Links

- Prior version-bump precedent: commit `28248b38f chore(a4): bump version to 15.0.0 for audience-split refactor` — established the per-feature bump pattern in marketplace.json.
- Audience-split refactor that preceded this work: commits `7020c0474`, `703902cc7`, `d83fff263`, `2ba53a878` (renamed `references/`→`authoring/`, `docs/`→`dev/`, split `workflows/`).

## Decisions and Rationale

- **Single coupled commit for the rename + reference sweep** — keeping rename and references in one commit avoids a transient state where references point at a moved file. The file move is a `git mv` so blame chains are preserved.
- **Procedure file `spawn-implementer.md` renamed too** — the user explicitly asked for it after I flagged the inconsistency with `run/SKILL.md`'s table cell label. Now the cell label and filename match.
- **`.handoff/` files deliberately not rewritten** — prior handoffs are point-in-time snapshots; updating them would be revisionist. Their banner literally says "DO NOT UPDATE THIS FILE."
- **SemVer minor over patch** — the `task-implementer` keyword appeared in the public-facing skill description (`run/SKILL.md` `description:` field, surfaced to triggering), so this is more than a purely internal rename. User confirmed minor.
- **Earlier in session: `Minimal shape via rules/ alone?` question** — concluded that rules/ covers authoring guidance only; ID allocation, file scaffolding, and `/a4:run` invocation are still needed. The user did not ask to act on that observation; left as discussion only.

## Important Dialog

- User: `plugins/a4/agents/task-implementer.md 는 coder로 이름 변경` — initial rename request, narrow scope.
- User: `1 변경 / 2. semver minor` — approving the two follow-on items I flagged (rename `spawn-implementer.md` and bump `a4.version`).
- Earlier: `workflows/ 아래 문서를 참조하는 skill 은?` — pure inventory question; answered with grep results, no file edits.

## Validation

- `grep -rln "task-implementer\|spawn-implementer" plugins/` → no matches (exit 1). Confirms the sweep was complete inside `plugins/`.
- `git status --short` → clean before handoff commit.
- `uv run plugins/a4/scripts/validate.py --list-checks` → ran (validator entrypoint healthy). The validator targets `<a4-dir>` workspaces, not plugin source; no workspace was modified, so a workspace-scoped run is not meaningful here.
- No skill or agent was actually invoked end-to-end. The rename is textual; the next time `/a4:run` spawns the agent, the `subagent_type: "a4:coder"` resolution will be exercised live.

## Known Issues and Risks

- **Live `/a4:run` not exercised post-rename.** If a workspace caches subagent ids or if there is any registry that pins the old name, the first real `/a4:run` invocation could fail to resolve `a4:coder`. Subagent discovery in this plugin is filename-based (`agents/<name>.md` + frontmatter `name:`), so this is low risk, but unverified.
- **`.handoff/2-…` and `.handoff/8-…` still mention `task-implementer`.** Intentional — they are historical. A reader new to the project may briefly be confused; the v15.1.0 entry in marketplace + this handoff frame the rename.
- **No CHANGELOG entry was added.** This repo does not appear to maintain one outside marketplace `version:` and commit messages. If a CHANGELOG is desired, that's net-new.

## Next Steps

1. Run `/a4:run` against a real workspace at least once to confirm `Agent(subagent_type: "a4:coder")` resolves and that the worktree-isolation flow still spawns. (Highest priority — only true validation of the rename.)
2. Decide whether to add a one-line note in `plugins/a4/README.md` (or its agents table) calling out the rename for downstream consumers, or treat the marketplace version bump as sufficient.
3. Consider whether `agents/test-runner.md`'s body still reads naturally now that its sibling is named `coder` (e.g., "unit tests are run by task-implementer" line was rewritten to `coder` — re-skim for any sentence that now scans awkwardly).

## Open Questions

- Should `Minimal shape entry skills` (`/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research`) cite `workflows/pipeline-shapes.md` even though the doc currently lists them as skills that **do not** cite it? The earlier discussion about "Minimal entry is mostly an authoring guide" surfaces the question but did not produce a decision.
- Is "coder" the right final name, or is it a stepping stone? "Implementer" → "coder" is one step; alternatives like "builder" or simply leaving it as the agent's primary verb were not explored.

## Useful Commands and Outputs

```bash
# Review the rename + sweep (file moves + token replacements)
git show 082a3c829

# Review the version bump
git show 0fcd2f25c

# Confirm no stale references remain in plugin source
grep -rln "task-implementer\|spawn-implementer" plugins/

# Inspect the renamed agent file
cat plugins/a4/agents/coder.md

# Inspect the renamed procedure file
cat plugins/a4/skills/run/references/spawn-coder.md

# Workspace validator (when a real a4 workspace exists)
uv run plugins/a4/scripts/validate.py <a4-dir>
```
