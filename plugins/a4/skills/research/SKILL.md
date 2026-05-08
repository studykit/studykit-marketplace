---
name: research
description: "Author a time-boxed written research task."
argument-hint: "[title or short description]"
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, TaskCreate, TaskUpdate, TaskList, WebSearch, WebFetch
---

# Single Research Task Author

Writes one `a4/research/<id>-<slug>.md`. The body is the deliverable — sources consulted, findings, options.

Seed: **$ARGUMENTS**

## Scope

- **In:** writing one research task file at `status: queued` / `progress` / `done`, allocating its id, capturing `mode:` (`comparative` | `single`) and `options:` (when comparative).
- **Out:** `implements:` / `spec:` / `cycle:` (all forbidden on research — cite triggering UCs/specs from `## Context` body prose if relevant), implement / test loop (`/a4:auto-coding`), discard (`/a4:discard`), reviewer (use `/a4:research-review` for the kind=research quality pass), authoring tasks of other families. No commit.

## Pre-flight

1. Resolve project root: `git rev-parse --show-toplevel`. If not a git repo, abort.
2. Verify `<project-root>/a4/` exists. If not, abort — this skill is workspace-scoped.
3. Ensure `<project-root>/a4/research/` exists. Create with `mkdir -p` if missing.

## Author Flow

Steps procedure: `references/author-flow.md`. Covers capture intent (mode, options) → compose body (Context + Options/Findings per mode) → allocate id + write → hand-off.

## Commit Points

`references/commit-points.md`.

## Wrap Up

When the task file is written:

1. Summarize: task id / title, mode (`single` / `comparative`), options if comparative.
2. Suggest the next step:
   - `queued` or `progress` → start the investigation directly (the user or an investigator agent fills `## Context` + `## Options`/`## Findings`); when finalized, optionally run `/a4:research-review` before flipping to `done`.
   - `done` → consider `/a4:research-review` for a quality pass.
3. Suggest `/a4:handoff` only if the broader session warrants a snapshot.

## Non-Goals

- Do not declare `implements:`, `spec:`, or `cycle:` on a research task — all three are forbidden.
- Do not run a reviewer agent inline. `/a4:research-review` is a separate quality pass.
- Do not author multiple research tasks in one invocation.
- Do not author non-research tasks here — use `/a4:task`, `/a4:bug`, or `/a4:spike`.
- Do not flip task status beyond the initial `open` / `queued` / `done` write.
- Do not make the decision in the research body. Research describes evidence; the decision belongs in a spec's `## Decision Log`.
