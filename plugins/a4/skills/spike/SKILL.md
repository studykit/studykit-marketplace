---
name: spike
description: "This skill should be used when the user wants to author a single spike task — a time-boxed exploration to unblock a decision (XP sense). PoC, investigation, benchmark — throwaway code. Common triggers: 'spike on X', 'add a spike', 'create a spike for', 'I need a quick PoC', 'investigate X technically before deciding', 'time-box an exploration'. Writes a4/spike/<id>-<slug>.md and proposes a project-root artifacts/spike/<id>-<slug>/ artifact directory for the throwaway code. `implements:` / `spec:` / `cycle:` are forbidden on spike. For pure written investigation without throwaway code, use /a4:research instead. Single-task entry. To discard a task use /a4:discard."
argument-hint: "[title or short description]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Spike Task Author

> **Authoring contract:** `${CLAUDE_PLUGIN_ROOT}/references/spike-authoring.md`. This skill orchestrates writing through that contract.

Writes one `a4/spike/<id>-<slug>.md` and proposes the accompanying artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/` for the throwaway PoC code.

`/a4:run` is the agent loop that consumes spike files this skill produces. This skill never spawns implementation agents itself.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one spike task file at `status: pending` (or `complete` for post-hoc), allocating its id, proposing the `artifacts/spike/<id>-<slug>/` artifact directory.
- **Out:** `implements:` / `spec:` / `cycle:` (all forbidden on spike — cite triggering specs from `## Description` body markdown links if relevant), implement / test loop (`/a4:run`), discard (`/a4:discard`), authoring tasks of other families. No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/spike/` exists. Create with `mkdir -p` if missing.

## Author Flow

Steps procedure: `references/author-flow.md`. Covers capture intent (hypothesis, decision the spike informs) → compose body → propose artifact directory → allocate id + write → artifact directory create → hand-off.

## Commit Points

`references/commit-points.md`. The single commit covers the new task file plus the empty artifact directory (with `.gitkeep` if added).

## Wrap Up

When the task file is written:

1. Summarize: task id / title, the question being explored, whether the artifact directory was created.
2. Suggest the next step: `pending` → `/a4:run`.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not declare `implements:`, `spec:`, or `cycle:` on a spike — all three are forbidden.
- Do not auto-archive `artifacts/spike/<id>-<slug>/` on completion. Archiving is a manual `git mv` to `artifacts/spike/archive/<id>-<slug>/`.
- Do not author multiple spikes in one invocation.
- Do not author non-spike tasks here — use `/a4:feature`, `/a4:bug`, or `/a4:research`.
- Do not flip task status beyond the initial `open` / `pending` / `complete` write.
- Do not write production source from a spike. PoC code belongs under `artifacts/spike/<id>-<slug>/`; if the outcome warrants production work, follow up with a `/a4:feature` task.
