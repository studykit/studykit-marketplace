# a4 — task authoring

A task at `a4/task/<id>-<slug>.md` is a **unit of regular implementation work** — new functionality, extension, or refactor. The default issue family in the Jira sense (equivalent to Jira's "Task" issue type alongside Bug / Story / Epic).

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders sharing the same lifecycle, each with its own authoring contract. Cross-family conventions for artifact directories: `./artifacts.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | queued | progress | holding | complete | failing | discarded
implements: []         # list of paths, e.g. [usecase/3-search-history]
depends_on: []         # list of paths to other tasks
spec: []               # list of paths, e.g. [spec/8-caching-strategy]
parent:                # optional: an issue (task / bug / spike / research) this task descends from
related: []            # catchall for cross-references
artifacts: []          # artifact paths under artifacts/task/<id>-<slug>/ (typically empty)
cycle: 1               # implementation cycle number
labels: []             # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `task` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `queued` \| `progress` \| `holding` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | specs governing this task |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this task descends from, **or** an `umbrella/<id>-<slug>` aggregating this task with siblings. Cross-type within the issue family is allowed (e.g., `parent: spike/12-cache-shape`). See "Parent and shared narrative" below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/task/<id>-<slug>/`. Empty list is the typical default. Production source paths are not duplicated in frontmatter; git history is authoritative, and the optional body `## Change Plan` serves as a forward-looking scope fence when needed. |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |


- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: task` is fixed for files under `a4/task/`. No `kind:` field — the type *is* the kind.
- `id:` see `./frontmatter-issue.md` § `id`.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare whenever UC-driven.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare in UC-less projects (the spec's `## Specification` body + relevant `architecture.md` section becomes the AC source).
- `implements:` and `spec:` are **optional and orthogonal** — zero, one, or both. See the smell check below for the zero-anchor case.
- `artifacts:` is artifact-only — paths must point under `artifacts/task/<id>-<slug>/...`. Typically empty for task work shipping only production source. Production source paths are not duplicated in frontmatter; git history is authoritative. The optional body `## Change Plan` may name them as a forward-looking scope fence. See "Artifacts directory" below.
- `cycle` starts at `1`; bumped on `failing → queued` next-cycle defers.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set when this task descends from another issue: a follow-up `task` from a `spike`, a `task` decomposed into smaller `task`s, a `task` spawned to fix a bug surfaced by another `task`. Cross-type within the issue family allowed.
- **Aggregation parent (umbrella)** — set to `umbrella/<id>-<slug>` when this task is one of several children grouped under an umbrella for shared narrative. See `./umbrella-authoring.md`.

The parent file is the agreed home for **narrative shared across siblings**. Record in the parent's `## Log`, not duplicated in each child. When a child entry depends on a parent decision, inline-cite the parent path per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`.

### `type: task` with empty `implements:` and `spec:` — smell check

A task with **both** anchors empty has no AC source. Either downgrade to `spike` (move file to `a4/spike/`, change `type:` to `spike`) if genuinely exploratory, or attach an anchor.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and batch-generated tasks without a UC group can legitimately stay anchorless. The deeper signal is in the body: when the description implies a user-facing scope no existing UC covers, or an architectural choice no existing spec records, surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`.

### Granularity — one cohesive unit per file

Each `a4/task/<id>-<slug>.md` is one cohesive unit. When a request, seed, or breakdown exceeds what fits cohesively in a single task — multiple unrelated edits, distinct AC sets, or independent test surfaces — split into multiple task files, one per cohesive unit. Each split file allocates its own globally-monotonic `id:` and stands on its own. Use `depends_on:` between split tasks when one must land before another, and a shared `parent:` (issue or `umbrella/<id>-<slug>`) when the siblings warrant cross-cutting narrative per `./umbrella-authoring.md`.

### Evidence-readiness — sister rule

Anchors decide where the AC comes from; **evidence** decides whether the task is actionable as a handoff. The two are independent — clean `implements:` / `spec:` does not make the task evidence-ready. Binding rule: `./spike-before-task.md` — five evidence categories (reproduce command, code coordinates, data flow, baseline, test fixture) are expected by the time the task is `queued`; when two or more are empty the parent issue family is `spike` (with a runnable artifact directory) or `research`, not `task`.

If implementation surfaces a real choice (architectural shape, protocol, format, schema) that no existing spec records — common in spec-less projects — spawn a spec at that point and add its path to `spec:`. See `./spec-authoring.md`; specs are not required to be heavy. Do **not** capture the decision inline in the task body (no `## Decision` section). Splitting decision rationale between task and spec breaks the audit trail and the supersede chain.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Task-specific notes:

- Batch-authored tasks use `open` as initial status; the user promotes them `open → queued` when ready for execution.
- `complete` means unit tests passed.
- `cycle:` bumps on `failing → queued` next-cycle defers.
- Required body sections for the `complete` preflight: `## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`. (`## Change Plan` is optional.)

## Body shape

**Required:**

- `## Description` — what and why.
- `## Unit Test Strategy` — scenarios + isolation strategy + test file paths.
- `## Acceptance Criteria` — checklist. AC source:

  | Shape | AC source |
  |---|---|
  | `implements: [usecase/...]` | UC `## Flow` / `## Validation` / `## Error Handling` |
  | `spec: [spec/...]` (UC-less) | spec `## Specification` body + relevant `architecture.md` section |

  AC source is a documentation convention. The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Change Plan` — forward-looking scope fence. Action / path / change table (or bullet list) listing production source paths the task plans to write or modify, plus any artifact paths under `artifacts/task/<id>-<slug>/`. Distinct from git history (which records changes *after the fact*); this section records what is *planned* before implementation. Useful when (a) the task is one of several in a batch and parallel coder agents need a per-task path-level scope fence, (b) the file set is non-obvious and warrants explicit handoff, or (c) the same file is touched by multiple sibling tasks (3+ overlap signals a shared integration point — see `./umbrella-authoring.md`). Skip for single-file or self-evident scope. Auto-populated by `/a4:breakdown` for batch-derived tasks.
- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`). For UC-less work, link to the spec or relevant `architecture.md` section.
- `## Resume` — current-state snapshot for the next session. Strongly recommended while non-terminal (any status other than `complete` / `discarded`). See `./issue-body.md#resume`.
- `## Log` — append-only narrative. Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`).

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A task may have a sibling artifact directory at `<project-root>/artifacts/task/<id>-<slug>/` when artifacts have evidentiary or comparative value — comparison test samples, execution outputs, design mockups, migration dry-run results:

```
<project-root>/
  a4/task/<id>-<slug>.md             # task markdown — type: task
  artifacts/task/<id>-<slug>/        # comparison samples, outputs, mockups (opt-in)
```

Optional and the exception, not the default. Use only when the artifacts themselves need to be preserved (before/after screenshots anchoring a UC's expected outcome, sample inputs/outputs proving a parser change). Production source the task ships is recorded by git history (and the optional body `## Change Plan` may name it for forward-looking scope-fencing); frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions live in `./artifacts.md` and apply to `type: task` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/task/` must declare `type: task`. Mismatched declarations are a folder-routing error.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Rely on git history (and the optional body `## Change Plan`).

## Don't (task-specific)

- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded`, UC `revising` → task `queued`-reset are the writer's job.
- **Don't author a different issue family here.** Move spikes to `a4/spike/`, bugs to `a4/bug/`, and research to `a4/research/`.
