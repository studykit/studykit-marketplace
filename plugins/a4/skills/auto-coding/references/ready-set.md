# Step 1: Pick Ready Tasks

## Pre-flight (parallel mode only; skipped in `serial` mode)

Before scanning the ready set:

```bash
local=$(git rev-parse HEAD)
origin=$(git rev-parse origin/HEAD)
test "$local" = "$origin" \
  || halt "push local commits to origin (or run 'git remote set-head origin -a' if origin's default branch changed) before running /a4:auto-coding"
```

Rationale and recovery in `./parallel-mode.md`. Serial mode skips this entirely — see `./serial-mode.md`.

## Ready definition

A task is **ready** when all of:

- `status ∈ {queued, failing}`
- every `depends_on` entry resolves to a task with `status: done`
- one of:
  - `implements:` is non-empty AND every UC in `implements:` has `status ∈ {ready, implementing}` (so `revising` / `discarded` / `blocked` / `superseded` / `shipped` UCs' tasks are skipped), OR
  - `implements:` is empty (UC-less task — spec-justified task, spike, or bug). Ready conditions vacuously pass; UC status checks do not apply.

Build the ready set by reading task + UC frontmatter.

## Parallelism

Independent ready tasks run in parallel. Tasks with mutual dependencies run sequentially.
