---
timestamp: 2026-04-27_1626
topic: run-parallel-isolation
---

> **DO NOT UPDATE THIS FILE.** This handoff is a point-in-time snapshot of the session at 2026-04-27_1626. To record a later state, create a new handoff file via `/handoff` — never edit this one.

# `/a4:run` parallel task-implementer worktree isolation — design ADRs final

## Why this thread exists

`plugins/a4/skills/run/SKILL.md` Step 2 explicitly permits parallel `task-implementer` agents ("Independent ready tasks run in parallel") and Step 4b's commit policy gives each task its own commit, but the SKILL.md does not specify any isolation mechanism. Without isolation, two parallel agents share a single working tree, staging area, and HEAD — so concurrent file edits race, `git add` / `git commit` collide on the index, and HEAD advances in nondeterministic agent-completion order.

This thread settles the isolation model and the surrounding commit / merge / cleanup contract, and lays the groundwork for a follow-up edit pass on `run/SKILL.md` and other a4 skills' `## Commit Points` sections.

## What landed in this session

Two ADRs in `plugins/a4/spec/` (status: `final`, both authored 2026-04-27):

1. `2026-04-27-a4-commit-message-convention.md` — workspace-wide commit subject form.
2. `2026-04-27-a4-run-parallel-task-implementer-isolation.md` — `/a4:run` Step 2 parallel execution model.

These are plugin meta-design ADRs (not user-workspace `a4/adr/` artifacts), so they have no `id:` frontmatter — date+slug is the identifier. The `plugins/a4/spec/` directory was empty before this session; these are the first two files in it. (One pre-existing reference `[[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]` exists in `run/SKILL.md` but the spec file itself was never written — that is pre-existing and not introduced or addressed here.)

### ADR 1: commit-message convention — chosen form

**ID-bearing commit** (one or more a4 workspace IDs touched):

```
#<id1> [#<id2> ...] <type>(a4): <description>
```

**ID-less commit** (no workspace artifact touched, e.g., wiki edits without a triggering review item, plugin-meta edits, build config):

```
<type>(a4): <description>
```

- Workspace IDs are globally monotonic across families (task / review / adr / usecase / idea / spark) so no type prefix on the id.
- Multiple ids are space-separated and appear before the type prefix.
- `merge` is added as a a4-specific Conventional Commits type for `/a4:run`'s `--no-ff` merge commits; existing types (`feat`/`fix`/`docs`/`refactor`/`chore`/`test`) remain.
- `git log --grep="#42"` returns the full lifecycle of a single artifact.

Rejected forms and rationale: see ADR 1 §Options Considered. Briefly: type-prefixed ids (`#task/42`) were rejected as redundant given global monotonic ids; trailing-id form (`(#42)`) was rejected for poor `git log --oneline` discoverability; trailer-line form (`Refs: #42`) was rejected for the same reason.

### ADR 2: parallel task-implementer worktree isolation — chosen model

| Aspect | Decision |
|---|---|
| Isolation | `Agent({ isolation: "worktree" })` per `task-implementer`; one worktree per parallel ready task |
| Pre-flight | At Step 1 entry, halt if `git rev-parse HEAD ≠ git rev-parse origin/HEAD`. User must push (or run `git remote set-head origin -a`) before re-invoking |
| Merge primitive | `git merge --no-ff -m "<conv-msg>"` per task branch |
| Merge order | Ascending `task.id` |
| Conflict policy | Halt + user resolve. No review item emitted |
| Progress unit | Partial: siblings that merged before the conflict stay on main + transition `→ complete`; the conflicting task's worktree/branch are preserved + task transitions `→ failing`; subsequent siblings are not attempted |
| `test-runner` invariant | Step 3 reachable only when every cycle ready task is integrated. Any merge sweep failure → Step 3 skipped, cycle ends in halt |
| Worktree cleanup (success) | `git worktree unlock <path> && git worktree remove --force <path> && git branch -D <branch>` |
| Worktree cleanup (failure) | Preserved for user diagnosis. `/a4:run iterate` may retry; orphans handled by Claude Code's startup sweep at `cleanupPeriodDays` |
| Branch-to-task mapping | In-memory `{taskId, agentId, worktreePath, worktreeBranch}` parsed from each Agent tool result's three trailing lines (`agentId:`, `worktreePath:`, `worktreeBranch:`). Permanent record in the merge commit's `#<id>` prefix |
| Serial fallback | `/a4:run --serial` (or `iterate serial` arg) opts into no-isolation, sequential mode for environments where worktree isolation is unavailable. Manual opt-in only |
| `.gitignore` | Projects should add `.claude/worktrees/` to `.gitignore`. ADR documents the recommendation; does not enforce |

Rejected forms (see ADR 2 §Options Considered): files-disjoint scheduling, lockfile-coordinated staging on a single tree, cherry-pick / squash / octopus merge, all-or-nothing rollback, test-merged-subset, WorktreeCreate-hook base-ref override, document-only convention.

## Empirical facts about `Agent({ isolation: "worktree" })`

Captured from a one-shot empirical test (single agent, this session) and the official docs at <https://code.claude.com/docs/en/common-workflows#run-parallel-claude-code-sessions-with-git-worktrees> and <https://code.claude.com/docs/en/sub-agents>. Reproduce or extend if needed in the next session.

- **Worktree path**: `<repo>/.claude/worktrees/agent-<random-hex>/`
- **Branch name**: `worktree-agent-<random-hex>` (the `<name>` portion equals the agentId)
- **Base ref**: `origin/HEAD`. Not local HEAD. This is the critical reason the pre-flight check exists.
- **No user control** over branch name, worktree name, or base ref via the Agent tool. For full base-ref control a `WorktreeCreate` hook is needed (deferred — Open Question in ADR 2).
- **Return value** appends three structured lines after the agent's body:
  ```
  agentId: <hex>
  worktreePath: <abs path>
  worktreeBranch: <branch name>
  ```
- **Lock state**: worktrees are git-locked while the agent runs; `git worktree remove` fails without `unlock` first. `--force` then handles any residual untracked content.
- **Auto-cleanup**: agent that makes no changes → worktree+branch removed automatically. Agent with changes → worktree persists; cleanup is the caller's responsibility (per `/a4:run`'s 3-step sequence above).
- **`.worktreeinclude`**: project-root file using gitignore syntax to copy gitignored files (`.env` etc.) into worktrees. Not adopted by `/a4:auto-bootstrap` yet — Open Question in ADR 2.
- **Concurrency**: untested at N>2 in this session. Behavior under git-index lock contention or disk pressure is unverified.

### Pitfall hit during the experiment (recorded so the next session avoids it)

The first experiment in this session forgot to pass `isolation: "worktree"` to the Agent tool calls. Five sibling agents all ran in the parent's working tree (`/Users/myungo/GitHub/studykit-plugins`) and committed directly to local `main`. Three commits and one untracked file landed before the mistake was caught. Cleanup was `git reset --hard 6483d1b48 && rm -f exp_c_bar.txt`, returning main to the pre-experiment HEAD. The actual `isolation: "worktree"` retest in this session was a single-agent confirmation, which produced the empirical facts above. Bottom line: the `isolation` parameter must be set explicitly on every `Agent` call in Step 2 — there is no project-level default the parent inherits.

## Where the work goes next

The two ADRs are design only. The skill source still describes the pre-ADR model. Follow-up edits required:

### `plugins/a4/skills/run/SKILL.md` — substantive rewrite

| Section | Edit |
|---|---|
| `argument-hint` (line 4) | Add `serial` as an optional arg |
| `## Workspace Layout` (~line 21) | No change |
| `## Launch & Verify Source` | No change |
| `## Mode Detection` | Add a Pre-flight item: `local HEAD == origin/HEAD` halt |
| `## Resume Hygiene` | Add a step: orphan worktree sweep is delegated to Claude Code's startup; `/a4:run` does not duplicate |
| `## Step 1: Pick Ready Tasks` | Add the pre-flight check at entry |
| `## Step 2: Spawn task-implementer` (~line 110–140) | Add `isolation: "worktree"` to every Agent call. Insert a new section "Step 2.5: Merge sweep" describing: parse return-value 3 lines, ascending-task-id `git merge --no-ff -m "#<id> merge(a4): integrate <slug>"`, partial-progress on conflict (halt, preserve failing worktree, transition `→ failing`), 3-step cleanup on success |
| `## Step 3: Run Integration + Smoke Tests` | Update to assert all-merged invariant (gate Step 3 entry on merge sweep success) |
| `## Iteration Entry` | Note re-attempt path: failing task's worktree branch may need `git merge --no-ff` retry after user resolves; otherwise the failing task drops back to `pending` and the next cycle re-spawns a fresh worktree |
| `## Commit Points` (~line 219) | Rewrite all message-form examples per the commit-message convention. UC ship: `#<id1> [#<id2> ...] docs(a4): ship UC <slugs>` (no longer `docs(a4): ship UC <ids>`); test-runner cycle commit: `#<r1> #<r2> ... chore(a4): cycle <N> test-runner findings`; merge commit: `#<id> merge(a4): integrate <slug>` |
| `## Out of Scope` / `## Non-Goals` | Add: serial mode is opt-in only, not auto-detected; LLM-driven semantic conflict resolution out of scope (separate ADR) |
| Wikilink the two ADRs | At top of file in the cross-reference list |

### Other a4 skills — `## Commit Points` sections

`grep -l '## Commit Points' plugins/a4/skills/*/SKILL.md` listed:

- `plugins/a4/skills/auto-usecase/SKILL.md`
- `plugins/a4/skills/roadmap/SKILL.md`
- `plugins/a4/skills/run/SKILL.md` (above)
- `plugins/a4/skills/task/SKILL.md`

Each needs its commit-message examples updated to follow the convention. Generic shape:

- ID-bearing examples → `#<id> <type>(a4): <description>` (single-id) or `#<id1> #<id2> ... <type>(a4): <description>` (multi-id)
- ID-less wiki edits stay as `<type>(a4): <description>`

The convention's Consequences section already names the `/a4:run` and `/a4:task` sites explicitly; `roadmap` and `auto-usecase` need the same audit pass.

### `plugins/a4/agents/task-implementer.md` — likely no edit needed, verify

Per ADR 2 §Scope: the agent commits in its current working tree, which becomes the worktree transparently. The agent does not need to know it is in a worktree. **However**, the agent's commit message contract should follow the commit convention — verify the agent's prompt names the form `#<id> <type>(a4): <description>` with the task's `id:` injected. If the prompt currently says only "commit code + unit tests" without specifying message form, add the convention.

### `plugins/a4/agents/test-runner.md` — no edit needed

Per ADR 2 §Scope: the all-merged invariant means test-runner always runs on a clean integrated tree. Its current contract (single working tree, build → integration → smoke) is consistent.

### Empirical follow-up (deferrable)

- Test concurrent N=4+ worktrees if `/a4:run` produces such ready sets in practice. Look for git-index lock contention, disk pressure, return-value parsing under interleaved completions.
- Test agent failure modes (return error, timeout, malformed result) to verify the `worktreePath: / worktreeBranch:` lines appear vs. absent, and confirm the "preserve on changes" rule holds for partial-state agents.

## Open questions (carried forward from the ADRs)

From ADR 2 (`2026-04-27-a4-run-parallel-task-implementer-isolation.md` §Open Questions):

- Trivial conflict auto-resolution (`git rerere`, import-merge heuristics) — Stage 1, deferred until usage data.
- LLM-driven semantic conflict resolver — Stage 3, requires separate ADR (review-schema expansion).
- Concurrent worktree limits — empirical test deferred.
- Agent-tool failure-mode semantics — empirical test deferred.
- `.worktreeinclude` policy / `/a4:auto-bootstrap` integration.

From ADR 1 (`2026-04-27-a4-commit-message-convention.md` §Open Questions):

- Commit-message validator (`.githooks/commit-msg`) — defer until violations show up.
- Very-large multi-id commits (>10 ids) — body-line listing vs. subject-line. Defer.
- Cross-workspace ID collision — separate ADR if/when it arises.

## Files of record

```
plugins/a4/spec/2026-04-27-a4-commit-message-convention.md             (created this session)
plugins/a4/spec/2026-04-27-a4-run-parallel-task-implementer-isolation.md (created this session)
plugins/a4/skills/run/SKILL.md                                         (next: substantive rewrite per ADR 2)
plugins/a4/skills/task/SKILL.md                                        (next: Commit Points update per ADR 1)
plugins/a4/skills/roadmap/SKILL.md                                     (next: Commit Points update per ADR 1)
plugins/a4/skills/auto-usecase/SKILL.md                                (next: Commit Points update per ADR 1)
plugins/a4/agents/task-implementer.md                                  (next: verify commit-message contract)
plugins/a4/agents/test-runner.md                                       (no edit; consistent with ADR 2)
```

## Pre-existing inconsistencies noted (not addressed)

- `plugins/a4/skills/run/SKILL.md` references `[[plugins/a4/spec/2026-04-25-a4-run-final-fallback-policy]]` (lines 43, 253) but the spec file does not exist. The reference is unrelated to this thread; leaving for the team to either author the missing ADR or remove the broken wikilinks.

## How to resume

Open `plugins/a4/skills/run/SKILL.md` and edit per the table in [Where the work goes next §run/SKILL.md](#plugins-a4-skills-run-skill-md--substantive-rewrite). Cross-reference both ADRs in the file's introduction. Once `run/SKILL.md` is internally consistent with the ADRs, sweep the other three SKILL.md `## Commit Points` sections for the convention. Verify `task-implementer.md`'s commit-message contract last.

The two ADRs are status: `final`. They should not be edited inline as part of the follow-up work; if a decision needs revision, author a new spec ADR that supersedes the relevant one (per the established a4 ADR pattern of authoring a new file, not in-place editing).
