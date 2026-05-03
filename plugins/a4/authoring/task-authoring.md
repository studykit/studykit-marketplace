# a4 — task authoring

A task at `a4/task/<id>-<slug>.md` is a **unit of regular implementation work** — new functionality, extension, or refactor. The default issue family in the Jira sense (equivalent to Jira's "Task" issue type alongside Bug / Story / Epic).

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders that share the same lifecycle but each has its own authoring contract. Cross-family conventions for artifact directories live in `./artifacts.md`.

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
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this task descends from, **or** an `umbrella/<id>-<slug>` aggregating this task with siblings. Cross-type within the issue family is allowed (e.g., `parent: spike/12-cache-shape`). See the "Parent and shared narrative" note below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/task/<id>-<slug>/`. Empty list is the typical default — task work that ships only production source. Production source paths the task writes or modifies are not duplicated in frontmatter; git history is the authoritative record, and the optional body `## Change Plan` section serves as a forward-looking scope fence when needed. |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |


- `title` is required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: task` is fixed for files under `a4/task/`. There is no `kind:` field — the type *is* the kind.
- `id:` see `./frontmatter-issue.md` § `id` for the allocator command and contract.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it whenever the project is UC-driven.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it in UC-less projects (the spec's `## Specification` body + relevant `architecture.md` section becomes the AC source).
- `implements:` and `spec:` are **optional and orthogonal** — a task may declare zero, one, or both. See the smell check below for the zero-anchor case.
- `artifacts:` is artifact-only — paths must point under `artifacts/task/<id>-<slug>/...`. The list is typically empty for task work that ships only production source. Production source paths the task writes or modifies are not duplicated in frontmatter; git history is the authoritative record. The optional body `## Change Plan` section may name them as a forward-looking scope fence when needed (see "Body shape" below). See "Artifacts directory" below for when to use the artifact directory.
- `cycle` starts at `1`; bumped on `failing → queued` next-cycle defers.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set it when this task descends from another issue: a follow-up `task` produced by a `spike`, a `task` decomposed into smaller `task`s, a `task` spawned to fix a bug surfaced by another `task`. Cross-type within the issue family (`task` / `bug` / `spike` / `research`) is allowed.
- **Aggregation parent (umbrella)** — set it to an `umbrella/<id>-<slug>` when this task is one of several children grouped under an umbrella for shared narrative. The umbrella file itself is purpose-built to hold cross-cutting decisions across siblings; see `./umbrella-authoring.md` for when to create an umbrella vs. when not to.

The parent file (issue or umbrella) is the agreed home for **narrative shared across siblings**. Record that narrative in the parent's `## Log`, not duplicated in each child. When a child `## Resume` or `## Log` entry depends on a parent decision, inline-cite the parent path in the child entry per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative` so a session reading the child file alone discovers the parent. Without that inline citation the parent's `## Log` is invisible to the reader.

### `type: task` with empty `implements:` and `spec:` — smell check

A task with **both** anchors empty has no AC source. Either downgrade to `spike` (and move the file to `a4/spike/`, changing `type:` to `spike`) if the work is genuinely exploratory, or attach an anchor.

Empty anchors are not always a problem — small UI tweaks, single-property validations, and batch-generated tasks without a UC group can legitimately stay anchorless. The deeper signal is in the body: when the description implies a user-facing scope no existing UC covers, or an architectural choice no existing spec records, surface the gap as a review item with `kind: gap`, `target: usecase/` or `target: spec/` (omit `target:` for cross-cutting), `source: task`, body specifying which upstream artifact appears missing.

### Granularity — one cohesive unit per file

Each `a4/task/<id>-<slug>.md` is one cohesive unit of implementation work. When a request, seed, or breakdown exceeds what fits cohesively in a single task — multiple unrelated edits, distinct AC sets, or independent test surfaces — split it into multiple task files, one per cohesive unit. Each split file allocates its own globally-monotonic `id:` and stands on its own (its own frontmatter, body, and AC). Use `depends_on:` between split tasks when one must land before another, and a shared `parent:` (issue or `umbrella/<id>-<slug>`) when the siblings warrant cross-cutting narrative per `./umbrella-authoring.md`.

### Evidence-readiness — sister rule

Anchors decide where the AC comes from; **evidence** decides whether the task is actionable as a handoff. The two are independent — a clean `implements:` / `spec:` does not make the task evidence-ready. Binding rule lives in `./spike-before-task.md`: five evidence categories (reproduce command, code coordinates, data flow, baseline, test fixture) are expected by the time the task is `queued`; when two or more are empty the parent issue family is `spike` (with a runnable artifact directory) or `research`, not `task`.

If implementation surfaces a real choice (an architectural shape, a protocol, a format, a schema) that no existing spec records — common in projects that started spec-less — spawn a spec at that point and add its path to this task's `spec:` frontmatter. See `./spec-authoring.md` for the spec body shape; specs are not required to be heavy. Do **not** capture the decision inline in the task body (no `## Decision` section, no rationale paragraph that belongs in a `## Decision Log`). Splitting decision rationale between task and spec breaks the audit trail and the supersede chain.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Task-specific notes:

- Batch-authored tasks use `open` as initial status; the user promotes them `open → queued` when ready for execution.
- `complete` means unit tests passed.
- `cycle:` bumps on `failing → queued` next-cycle defers.
- Required body sections for the `complete` preflight: `## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`. (`## Change Plan` is optional — see "Body shape" below.)

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

- `## Change Plan` — forward-looking scope fence. Action / path / change table (or bullet list) listing the production source paths the task plans to write or modify, plus any artifact paths under `artifacts/task/<id>-<slug>/` when the task uses an artifact directory. Distinct from git history (which records what was changed *after the fact*); this section records what is *planned* before implementation begins. Useful when (a) the task is one of several in a batch and parallel coder agents need a per-task path-level scope fence, (b) the file set is non-obvious and warrants explicit handoff to the implementer, or (c) the same file is touched by multiple sibling tasks (3+ overlap signals a shared integration point — see `./umbrella-authoring.md`). Skip for single-file or self-evident scope; rely on `## Description` + `## Acceptance Criteria` and let git history record the actual changes. Auto-populated by `/a4:breakdown` for batch-derived tasks.
- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`). For UC-less work, link to the spec or relevant `architecture.md` section.
- `## Resume` — current-state snapshot for the next session: current approach, current blocker, open questions, next step. Freely rewritten as work progresses. Strongly recommended while the task is non-terminal (any status other than `complete` / `discarded`). See `./issue-body.md#resume`.
- `## Log` — append-only narrative of meaningful events (decision pivots, blocker resolutions, approach changes worth remembering). Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A task may have a sibling artifact directory at `<project-root>/artifacts/task/<id>-<slug>/` when artifacts have evidentiary or comparative value — comparison test samples, execution outputs, design mockups, migration dry-run results:

```
<project-root>/
  a4/task/<id>-<slug>.md             # task markdown — type: task
  artifacts/task/<id>-<slug>/        # comparison samples, outputs, mockups (opt-in)
```

Optional and the exception, not the default — most tasks have no artifact directory. Use it only when the artifacts themselves need to be preserved (before/after screenshots that anchor a UC's expected outcome, sample inputs/outputs proving a parser change). Production source the task ships is recorded by git history (and the optional body `## Change Plan` may name it for forward-looking scope-fencing); frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions for the artifact directory — per-type expectations, the `artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in `./artifacts.md` and apply to `type: task` as written there.

## Common mistakes (task-specific)

- **Required section missing** (`## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/task/` must declare `type: task`. Mismatched declarations are a folder-routing error and should be re-located.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Production source paths are not duplicated in frontmatter; rely on git history (and, when forward-looking scope-fencing is needed, the optional body `## Change Plan` section).

## Don't (task-specific)

- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded`, UC `revising` → task `queued`-reset are the writer's job.
- **Don't author a different issue family here.** Move spikes to `a4/spike/`, bugs to `a4/bug/`, and research to `a4/research/` so the matching authoring contract applies.
