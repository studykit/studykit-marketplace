# Step 1: Pick Ready Tasks

## Pre-flight (parallel mode only; skipped in `serial` mode)

Before scanning the ready set:

```bash
local=$(git rev-parse HEAD)
origin=$(git rev-parse origin/HEAD)
test "$local" = "$origin" \
  || halt "push local commits to origin (or run 'git remote set-head origin -a' if origin's default branch changed) before running /a4:run"
```

Rationale and recovery in `./parallel-isolation.md`.

## Ready definition

A task is **ready** when all of:

- `status ∈ {pending, failing}`
- every `depends_on` entry resolves to a task with `status: complete`
- one of:
  - `implements:` is non-empty AND every UC in `implements:` has `status ∈ {ready, implementing}` (so `revising` / `discarded` / `blocked` / `superseded` / `shipped` UCs' tasks are skipped), OR
  - `implements:` is empty (UC-less task — spec-justified feature, spike, or bug). Ready conditions vacuously pass; UC status checks do not apply.

Build the ready set by reading task + UC frontmatter.

## Parallelism

Independent ready tasks run in parallel. Tasks with mutual dependencies run sequentially.
