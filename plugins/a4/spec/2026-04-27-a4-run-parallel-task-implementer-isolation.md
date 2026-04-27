---
title: "/a4:run parallel task-implementer worktree isolation"
status: final
created: 2026-04-27
updated: 2026-04-27
---

# /a4:run parallel task-implementer worktree isolation

## Context

`/a4:run` Step 2 spawns one `task-implementer` agent per ready task and explicitly permits parallel execution: "Independent ready tasks run in parallel" (`plugins/a4/skills/run/SKILL.md` Step 1). Each `task-implementer` is contracted to commit its own code + unit tests as a single per-task commit.

The current SKILL.md does not specify any isolation mechanism. Without isolation, parallel agents share a single working tree, staging area, and HEAD. This admits several silent failure classes:

- Two agents editing the same file: last write wins, intermediate states are lost.
- Two agents staging concurrently: one agent's untracked files bleed into another's commit.
- HEAD advances unpredictably as commits land in the order agents finish, which is non-deterministic.

Claude Code provides `Agent({ isolation: "worktree" })`, which spawns each subagent in its own git worktree under `<repo>/.claude/worktrees/agent-<random-hex>/` on a branch named `worktree-agent-<random-hex>`. The worktree is created from `origin/HEAD` and is automatically cleaned up if the agent makes no changes. (Verified against the Claude Code documentation at <https://code.claude.com/docs/en/common-workflows> and <https://code.claude.com/docs/en/sub-agents>, plus a one-shot empirical test: a single isolated agent reported `pwd: <repo>/.claude/worktrees/agent-<hex>`, branch `worktree-agent-<hex>`, base commit equal to `origin/HEAD`, and the parent's `git worktree list` showed both the main checkout and the isolated worktree side-by-side.)

The Agent tool returns three structured lines after the agent's body output:

```
agentId: <hex>
worktreePath: <absolute path>
worktreeBranch: <branch name>
```

`/a4:run` parses these to map each task back to its worktree branch.

This ADR fixes the parallel execution model for `/a4:run` Step 2 and the post-loop integration sequence (merge sweep → test-runner). Commit-message form is governed by [`2026-04-27-a4-commit-message-convention`](./2026-04-27-a4-commit-message-convention.md) and is not redefined here.

## Decision

### Isolation model

Each `task-implementer` agent is spawned with `isolation: "worktree"`. Every parallel agent works in its own worktree off `origin/HEAD`. The parent `/a4:run` session never has parallel agents writing to the same working tree.

A `--serial` opt-in is supported as a fallback (see Serial fallback below) for environments where worktree isolation is unavailable or undesired.

### Pre-flight: local HEAD must equal `origin/HEAD`

Worktrees branch from `origin/HEAD` (Claude Code default), not from the local working-tree HEAD. If the user's local main is ahead of `origin/HEAD`, every spawned worktree starts on a stale base and the resulting commits would diverge from the user's actual work.

`/a4:run` therefore halts at session start when local HEAD differs from `origin/HEAD`:

```bash
local=$(git rev-parse HEAD)
origin=$(git rev-parse origin/HEAD)
test "$local" = "$origin" || halt "push local commits to origin (or run 'git remote set-head origin -a' if origin's default branch changed) before running /a4:run"
```

The check is at the start of Step 1 (pick ready tasks), before any agent spawn.

### Merge primitive: `git merge --no-ff`

After all `task-implementer` agents return, `/a4:run` performs a merge sweep against the local main checkout. Each successful task branch is integrated with `git merge --no-ff -m "<commit-message-convention message>"`. Reasons:

- Preserves the task commit's hash on main (the worktree's task commit becomes a parent of the merge commit, not rewritten).
- The merge commit explicitly marks "this is the integration boundary for task `#<id>`," visible in `git log --graph` and addressable with `git log --first-parent` for cycle-level history.
- `git bisect` with `--first-parent` walks task-level units, not internal task commits.
- "One task = one commit" remains true (one task commit + one merge commit per task; the merge commit is bookkeeping, not a content-level change).

Cherry-pick was considered and rejected: cherry-pick rewrites the task commit's hash on main and erases the worktree branch boundary from history. See [Options Considered](#options-considered).

### Merge order: ascending task id

Sibling task branches are integrated in ascending `task.id` order. Merge order is observable in `git log` output, so a deterministic order makes successive `/a4:run` invocations reproducible and easier to bisect when something goes wrong.

The order has no functional impact when all merges are conflict-free (sibling tasks are independent by definition of the ready set), but it does affect which merge fails first when a conflict exists.

### Conflict policy: halt + user resolve, no review item

A merge conflict during the sweep halts the run. The user resolves the conflict with standard git tooling and re-invokes `/a4:run iterate` to resume. No review item is emitted for the conflict. Reasons:

- Merge conflicts are immediate-decision items, not asynchronous backlog. Recording them in `a4/review/` would mix VCS-state issues with artifact-spec gaps and dilute the review queue's meaning.
- The halt message identifies the conflicting task and file directly; a separate review file adds no information.
- Existing skill halt patterns (strong upstream finding, 3-cycle limit) already use `halt + user resolve` semantics, so this remains consistent.

### Partial-progress unit: success integrated, failure preserved

When N sibling task branches are merged in id order and one fails the merge sweep:

- All sibling branches that successfully merged before the failure remain on main; their tasks transition to `complete`.
- The task whose merge conflicted: its worktree and branch are preserved (unmerged on main); its task transitions to `failing`; `/a4:run` halts.
- Subsequent siblings that have not yet been attempted: not integrated; their tasks remain at `progress` until `/a4:run iterate` resumes the sweep.

Rationale: maximize forward progress per cycle without compromising the integrity of the integrated subset, and preserve the failing worktree for user diagnosis.

### test-runner invariant: all-merged-or-halt

`/a4:run` Step 3 (test-runner spawn) is reachable only when every ready task in the cycle has been integrated into local main. If the merge sweep produced any failure, Step 3 is skipped; the cycle ends in halt.

Rationale: `test-runner` runs build + integration + smoke against a single working tree (per `plugins/a4/agents/test-runner.md` Step 1). It maps failures to a task via the task's declared `files:`. A partially-integrated tree breaks this mapping (a failure caused by a missing-because-conflicted task cannot be cleanly attributed). Forcing a clean integration before testing keeps `target:` attribution honest.

### Worktree cleanup

After a successful merge of a task's worktree branch:

```bash
git worktree unlock <worktreePath>
git worktree remove --force <worktreePath>
git branch -D <worktreeBranch>
```

`unlock` is required because the Agent tool locks the worktree for the duration of the agent's run; `--force` covers any residual untracked files inside the worktree. `branch -D` is safe because the branch's commits are now reachable from main via the merge commit.

After a failing merge:

- The worktree and branch are **not** cleaned up. They persist for user diagnosis.
- `/a4:run iterate` may re-attempt the merge after the user resolves the conflict, or the user may discard the worktree manually.

Orphaned worktrees (created by an agent that crashed or was interrupted before the merge sweep): Claude Code's startup sweep removes them automatically once they are older than `cleanupPeriodDays` and have no uncommitted changes / untracked files / unpushed commits. `/a4:run` does not duplicate this sweep.

### Branch-to-task mapping

Worktree branch names are not user-controllable and carry no task information. `/a4:run` records the mapping in-memory at spawn time:

```
{ taskId, agentId, worktreePath, worktreeBranch } per task
```

The mapping is parsed from each Agent tool result's three trailing lines (`agentId:`, `worktreePath:`, `worktreeBranch:`). The mapping persists for the duration of the `/a4:run` invocation, drives the merge sweep, and feeds the merge commit message (which is the only persistent record of the task→branch link, via the commit-message convention's `#<id>` prefix).

### Serial fallback

`/a4:run --serial` (or `/a4:run iterate serial`) opts into a no-isolation mode for environments where worktree isolation is unavailable or unwanted:

- `task-implementer` agents are spawned without `isolation: "worktree"` and one at a time.
- Each agent commits directly to local main (no merge sweep, no merge commit).
- All other rules in this ADR (test-runner invariant, conflict halt, partial-progress unit) collapse to trivial cases since there is only one in-flight task.

Serial mode is opt-in only. `/a4:run` does not auto-detect worktree availability or auto-fall-back; the user must request it explicitly.

### `.gitignore`

a4-using projects should add `.claude/worktrees/` to their `.gitignore`. `/a4:auto-bootstrap` (or, lacking that, the project's onboarding documentation) advises this; this ADR does not enforce it programmatically.

## Scope

Applies to:

- `plugins/a4/skills/run/SKILL.md` Step 2 (spawn task-implementer), Step 3 (test-runner invariant), the merge sweep that sits between Steps 2 and 3 in the new model, and the `## Commit Points` section.
- `/a4:run iterate` resume semantics: re-evaluate the ready set, re-run pre-flight, retry the merge sweep on preserved failing-task worktrees.

Does not apply to:

- Other a4 skills' commits (governed by the commit-message convention ADR alone).
- `/a4:roadmap`, `/a4:task`, and other authoring skills, which do not spawn agents or commit code.
- The `task-implementer` agent's internal logic (it remains contracted to "implement code, write unit tests, commit, return"). The agent does not need to know it is in a worktree; it just commits in its current working tree as before.

## Options Considered

### Isolation model

- **A. Worktree per task-implementer (chosen)** — each agent gets its own working tree and branch. Eliminates concurrent-write races at the cost of an explicit merge sweep.
- **B. Files-disjoint scheduling on a single tree** — the ready set is filtered so only tasks with non-overlapping `files:` lists run in parallel. Rejected: depends on `task.files:` being exhaustive (often it is not — task-implementers add imports, edit configs, etc.), and staging-area races persist regardless.
- **C. Full serialization** — no parallelism. Simple, but loses throughput. Retained as opt-in fallback (`--serial`).
- **D. Lockfile-coordinated staging on a single tree** — agents share the working tree but coordinate `git add` / `git commit` via a mutex. Rejected: working-tree edits remain raceful (Edit/Write tools have no inter-agent ordering guarantee); the protocol adds complexity for incomplete safety.

### Merge primitive

- **(i) `git merge --no-ff` (chosen)** — preserves task-commit hash, marks integration boundaries, supports first-parent traversal.
- **(ii) `git cherry-pick`** — single commit per task on main, linear history. Rejected: rewrites task-commit hash, erases worktree branch boundary from `git log --graph`, and is semantically "borrowing a commit from another branch" rather than "integrating a work unit," which mismatches the worktree model.
- **(iii) `git merge --squash`** — squashes the worktree branch into one commit on main. Rejected: identical end-state to cherry-pick when each task already produces a single commit, with the same loss of branch boundary.
- **(iv) `git merge --no-ff` with octopus** — merge all sibling branches in one commit. Rejected: octopus fails on any conflict, forcing a fallback path; the per-task merge model handles partial progress more naturally.

### Conflict handling

- **Halt + user resolve, no review item (chosen)** — fits a4's existing halt-on-strong-signal patterns; keeps `a4/review/` semantically clean.
- **Emit a review item with `source: run-merge`** — partially considered. Rejected: introduces a "merge conflict" review category that mixes VCS-state with artifact-spec gaps; the halt message already names the conflicting task and file.
- **Auto-resolve trivial conflicts via `git rerere` or import-merge heuristics** — deferred to a future Stage. Tracked in [Open Questions](#open-questions).
- **All-or-nothing rollback (reset main on any conflict)** — rejected: contradicts the partial-progress unit; rollback is destructive and risks racing with concurrent user commits.

### Partial-progress unit

- **Partial progress (chosen)** — successful sibling merges stay on main; failing sibling preserved unmerged.
- **All-or-nothing** — every sibling either lands or none does. Rejected: implies rollback (destructive), and removes the per-cycle forward progress that the parallelism is supposed to deliver.
- **Test-merged-subset** — Step 3 runs on the partially-integrated tree. Rejected: breaks `test-runner`'s `target:` mapping (a failure caused by a missing task cannot be attributed cleanly); requires a "subset" mode in `test-runner` that does not currently exist.

### Base ref handling

- **Pre-flight halt on local ≠ `origin/HEAD` (chosen)** — user pushes (or syncs `origin/HEAD`) before running. Single-line invariant; cheap to check.
- **WorktreeCreate hook overriding base to local HEAD** — viable but moves complexity into hook configuration. Deferred; pre-flight halt is sufficient and explicit.
- **Document-only convention** — rejected: silent stale-base bugs are exactly the failure mode this ADR exists to prevent.

## Consequences

- `plugins/a4/skills/run/SKILL.md` requires substantive edits to Steps 1–3, the `## Iteration Entry` section, the `## Commit Points` section, and the `## Out of Scope` / `## Non-Goals` lists. Notable additions:
  - Pre-flight `local HEAD == origin/HEAD` check at session start.
  - Merge sweep step inserted between current Steps 2 and 3.
  - Worktree cleanup step (success: 3-step; failing: preserved).
  - `--serial` fallback flag in `argument-hint`.
  - References to this ADR by wikilink.
- `plugins/a4/agents/task-implementer.md` (if it exists) does **not** need to change: the agent commits in its current working tree, which is now the worktree, transparently.
- `plugins/a4/agents/test-runner.md` does not change: the invariant guarantees it always runs on a fully-integrated main.
- The user-facing commit history gains one merge commit per task, in addition to the task commit. `git log --oneline --first-parent` shows the cycle-level history (one merge commit per task); `git log --oneline` shows full detail.
- `git log --grep="#<id>"` (per the commit-message convention) returns the task commit + the merge commit + any subsequent revision commits, giving a complete artifact-level history.
- `cleanupPeriodDays` (Claude Code setting) becomes load-bearing for orphan-worktree garbage collection. Default is 30 days; users on aggressive disk constraints may want to reduce it.
- Adding `.claude/worktrees/` to project `.gitignore` is the user's responsibility; the spec does not enforce it. A typical first run leaves no artifact in the repository's tracked tree, but a crash mid-cycle could leave an orphan worktree visible as untracked content until cleanup.

## Open Questions

- **Trivial conflict auto-resolution.** A future Stage 1 could enable `git rerere` and treat single-line / import-only conflicts as auto-resolvable. The auto-resolution would happen in the merge sweep; the resulting commit would record "auto-resolved <kind> conflict" in its body. Deferred until usage data justifies the additional surface area.
- **LLM-driven semantic conflict resolution.** A future Stage 3 could delegate semantic conflicts to an LLM-driven resolver that emits a review item with `source: merge-resolver` for post-hoc human audit. This expands the review-item schema's meaning ("findings + audit trails") and warrants a separate ADR.
- **Concurrent worktree limits.** `Agent({ isolation: "worktree" })` was empirically tested with one isolated agent (single-shot). Behavior under high concurrency (N=4+ simultaneous worktrees) — git-index lock contention, disk pressure on large repositories, Claude Code session-state limits — is unverified. Tracking item: if `/a4:run` produces ready sets larger than ~4 in practice, run an empirical test before relying on the parallelism in production.
- **Failure semantics of the Agent tool.** When a `task-implementer` errors, times out, or returns a malformed result, the docs state the worktree persists if changes exist. The exact discrimination between "agent failed cleanly" and "agent left partial state" is unverified and may need an empirical test or a defensive `git status` check inside the worktree before deciding cleanup vs. preservation.
- **`.worktreeinclude` policy.** Projects that need `.env` (or other gitignored files) inside worktrees can list them in a project-root `.worktreeinclude`. Whether `/a4:auto-bootstrap` should generate this file (and from what signal) is a separate question; not addressed here.
