# Step 3: Derive Tasks

Enter plan mode (`EnterPlanMode`). Inspect the candidate behavior, relevant supporting documents, and the codebase, then design one task entry per executable unit. Nothing is written until plan mode exits.

## 1. Identify the candidate set

Walk behavioral inputs and **skip** material already covered by an existing task:

- **UC coverage** — for every `a4/usecase/<id>-<slug>.md`, check whether any existing `a4/task/*.md` has it in `implements:`.
- **Spec coverage** — for every `a4/spec/<id>-<slug>.md` at `status: active` (ignore `draft`; `superseded` is terminal), check whether any existing task has it in `spec:`.

The **candidate set** = UCs and specs not yet covered. If empty, report that all behavioral sources are already covered and exit without writing.

## 2. Select supporting references

For each candidate or candidate group, identify documents the future implementer must read to implement without guessing.

Reference classes:

- **a4 wiki pages** — `architecture.md`, `domain.md`, `actors.md`, `nfr.md`, `context.md`, and any other root `a4/*.md` page.
- **a4 issue-side evidence** — relevant `research/`, `spike/`, `review/`, or existing `task/` files.
- **Repository docs** — `README*`, `docs/**/*.md`, `adr/**/*.md`, `adrs/**/*.md`, or local equivalents discovered by `Glob` / `Grep`.

Selection rule: cite a supporting reference only when it changes implementation choices, terminology, file mapping, interface contracts, dependency ordering, or test strategy. Do not cite broad background docs just because they exist.

Use:

- Frontmatter `related:` for a4 path references that should be machine-searchable (`architecture`, `domain`, `research/<id>-<slug>`, `spike/<id>-<slug>`, etc.).
- Body `## References` for both a4 backlinks and repo-doc links, with one short note explaining why each matters.

Supporting references never replace `implements:` / `spec:`. Acceptance criteria still come from the UC/spec anchors and the task body.

## 3. Group candidates into tasks

A task can deliver one or more candidates. Apply `./planning-guide.md`:

- 1–5 related UCs / specs per task.
- Touches 1–3 components.
- Independently testable against `ci.md` `## How to run tests`.
- Roughly ≤ ~500 lines of new or changed code.

When one UC is large enough to split, multiple tasks may list the same UC in `implements:` and each task's Description / AC must state its slice.

## 4. Per-task fields and sections

For every derived task, populate:

- **`type: task`**, **`status: open`**.
- **`implements:`** — `usecase/<id>-<slug>` paths this task delivers. Empty when purely spec-driven.
- **`spec:`** — `spec/<id>-<slug>` paths this task realizes. Empty when purely UC-driven.
- **`related:`** — a4 supporting references selected in step 2. Omit if empty. Do not put repo docs here; use `## References`.
- **`depends_on:`** — prerequisite task paths from candidate grouping and codebase dependency analysis.
- **`## Description`** — what this task delivers, its slice when sharing a UC/spec with siblings, and any shared integration pattern.
- **`## References`** — supporting docs the implementer should read before implementation. Format each bullet as a backlink or repo path plus why it matters, e.g. ``- `../architecture.md#sessionservice` — component boundary and ownership.`` or ``- `../../docs/auth.md` — provider callback contract.`` Omit if no supporting docs apply.
- **`## Change Plan`** — explicit per-task scope fence, auto-filled from codebase exploration. Use concrete Action / Path / Change rows per `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`.
- **`## Acceptance Criteria`** — measurable checklist derived from UC `## Flow` / `## Validation` / `## Error Handling` and spec `## Specification`. Reference `ci.md` commands when AC names a runnable check.
- **`## Unit Test Strategy`** — scenarios, isolation, and test file paths.

The reverse view (which tasks implement a UC or realize a spec) is computed on demand by `search.py`; do not edit UC/spec files for backlinks.

## 5. Shared integration points

Identify files appearing in 3+ tasks' `## Change Plan`. Define the integration pattern in each contributing task's `## Description` so every implementer sees both its piece and the whole-file composition.

Example:

```text
Shared file: src/webview/main.ts
Integration pattern: Message handler registration + DOM component mounting.
This task's contribution: <task-specific piece>.
Other contributors: task/<id1>, task/<id2>, task/<id3>.
```

## 6. Duplicate detection

Before writing, compare drafts against existing `task/`, `bug/`, `spike/`, and `research/` files:

- **Identical anchors** — proposed `implements:` / `spec:` set fully overlaps an existing task → skip.
- **Title near-match** — slug overlap > 50% → skip with note.
- **File set overlap** — proposed `## Change Plan` paths fully covered by an existing issue-family file → skip with note.

Skipped candidates appear in the wrap-up summary.

## 7. Write artifacts

Exit plan mode.

- Allocate one id per new task in declaration order via `allocate_id.py`.
- Write each `a4/task/<id>-<slug>.md` per `${CLAUDE_PLUGIN_ROOT}/authoring/task-authoring.md`.
- Do not write wiki pages or append wiki `## Change Logs`.

## Summary message

After writing, emit:

```text
breakdown summary:
  candidates: <N> (UCs: <a>, specs: <b>)
  new tasks: <M> (#<id1>–<idK>)
  skipped: <S> (anchor / title / files overlap)
  supporting docs cited: <count>
  shared integration points: <count>
  next: spawn breakdown-reviewer (Step 4)
```

The substantive output is the task files.
