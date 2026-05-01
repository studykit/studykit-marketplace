# Step 3: Derive Tasks

Enter plan mode (the `EnterPlanMode` Claude Code primitive). Inspect the upstream material against the codebase, then design the task set. The output of this step is a draft of one task entry per executable unit; nothing is written until plan mode exits.

## 1. Identify the candidate set

Walk the behavioral inputs and **skip** material already covered by an existing task:

- **UC coverage** — for every `a4/usecase/<id>-<slug>.md`, check whether any existing `a4/task/*.md` has it in `implements:`. If yes, the UC is covered.
- **Spec coverage** — for every `a4/spec/<id>-<slug>.md` at `status: active` (specs at `draft` are not yet stable enough; `superseded` is terminal), check whether any existing task has it in `spec:`.

The **candidate set** = UCs and specs not yet covered. If the candidate set is empty, surface a summary message ("all behavioral sources already covered by existing tasks") and exit without writing.

## 2. Group candidates into tasks

A task can deliver one or more candidates. Apply the sizing guidance from `./planning-guide.md`:

- 1–5 related UCs / specs per task.
- Touches 1–3 components.
- Independently testable against `bootstrap.md` `## Verify`.
- Roughly ≤ ~500 lines of new or changed code.

When a single UC's flow is large enough to warrant splitting, the split is across tasks (one UC may appear in multiple tasks' `implements:`).

## 3. Per-task fields

For every task in the derived batch, populate:

- **`type: task`**, **`status: open`** (initial lifecycle state — see `../../../authoring/task-authoring.md` § Lifecycle).
- **`implements:`** — list of `usecase/<id>-<slug>` paths the task delivers. Auto-filled from the candidate grouping. Empty list when the task is purely spec-driven.
- **`spec:`** — list of `spec/<id>-<slug>` paths the task realizes. Auto-filled from the candidate grouping. Empty when purely UC-driven.
- **`depends_on:`** — `task/<id>-<slug>` paths for prerequisite tasks (this batch's tasks plus existing tasks the new ones rely on). Derived from the candidate grouping plus codebase imports.
- **`## Description`** — short narrative of what this task delivers, written against the upstream sources' Flow / Validation / Specification.
- **`## Files`** — auto-filled from Step 2 codebase exploration. Format per `../../../authoring/task-authoring.md` § Body shape (Action / Path / Change table). Best-effort hints; reviewers and the user iterate before promotion.
- **`## Acceptance Criteria`** — derived from each `implements:`'s UC `## Flow` / `## Validation` / `## Error Handling` and each `spec:`'s `## Specification`. Reference `bootstrap.md` `## Verify` commands when AC names a runnable check.
- **`## Unit Test Strategy`** — scenarios + isolation per `../../../authoring/task-authoring.md`.

The reverse view (which tasks implement a UC, which tasks realize a spec) is computed on demand by `search.py` — there is no UC / spec frontmatter field to refresh.

## 4. Shared Integration Points

Identify any file appearing in 3+ tasks' `## Files`. Define the integration pattern explicitly in each contributing task's `## Description` so each `coder` agent sees it. Without this, parallel coder agents land conflicting partial implementations on the shared file.

## 5. Duplicate detection (idempotency)

Before writing any task, compare the draft against existing tasks across all four issue family folders (`task/`, `bug/`, `spike/`, `research/`):

- **Identical anchors** — proposed task `implements:` / `spec:` set fully overlaps an existing task → **skip** (the existing task already covers it).
- **Title near-match** — slug overlap > 50% with an existing task → **skip with note** (the user should manually merge if they want the new framing).
- **File set overlap** — proposed `## Files` paths fully covered by an existing task → **skip with note** (likely the same change scope under different framing).

Skipped candidates appear in the wrap-up summary so the user can decide whether to discard or repurpose them.

## 6. Write artifacts

Exit plan mode.

- Allocate ids via `allocate_id.py` (one call per new task, in declaration order).
- Write each `a4/task/<id>-<slug>.md` per `../../../authoring/task-authoring.md`.
- Do not write any wiki page. Do not append `## Change Logs` to any wiki — this skill no longer owns one.

## Summary message

After writing, emit a summary covering:

```
breakdown summary:
  candidates: <N> (UCs: <a>, specs: <b>)
  created: <M> tasks (#<id1>–<idK>)
  skipped: <S> (anchor / title / files overlap)
    - <reason> for <candidate path>
  shared integration points: <count>
  next: spawn breakdown-reviewer (Step 4)
```

The summary is conversational; the substantive output is the new task files.
