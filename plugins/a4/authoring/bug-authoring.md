# a4 — bug authoring

A bug at `a4/bug/<id>-<slug>.md` is a **defect fix** — production code change against expected behavior. Not throwaway.

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders that share the same lifecycle but each has its own authoring contract. Cross-family conventions for artifact directories live in `./artifacts.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: bug
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | pending | progress | complete | failing | discarded
implements: []         # list of paths, e.g. [usecase/3-search-history]
depends_on: []         # list of paths to other tasks
spec: []               # list of paths, e.g. [spec/8-caching-strategy]
parent:                # optional: an issue (task / bug / spike / research) this bug descends from
related: []            # catchall for cross-references
artifacts: []          # artifact paths under artifacts/bug/<id>-<slug>/ (typically empty)
cycle: 1               # implementation cycle number
labels: []             # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `bug` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered (often empty for bug work that does not implement a UC) |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | specs governing this task |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this bug descends from, **or** an `umbrella/<id>-<slug>` aggregating this bug with siblings. Cross-type within the issue family is allowed. See the "Parent and shared narrative" note below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/bug/<id>-<slug>/` (typically empty — repro/logs/screenshots only when worth keeping) |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |


- `title` is required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: bug` is fixed for files under `a4/bug/`. There is no `kind:` field — the type *is* the kind.
- `id:` see `./frontmatter-issue.md` § `id` for the allocator command and contract.
- `implements:` lists `usecase/<id>-<slug>` paths the task delivers. Declare it when the bug traces to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths backing the task. Declare it when the bug is a regression against a spec's expected behavior.
- `implements:` and `spec:` are **optional and orthogonal** — a bug may declare zero, one, or both. Empty anchors are common for cross-cutting fixes.
- `artifacts:` is artifact-only — paths must point under `artifacts/bug/<id>-<slug>/...`. The list is typically empty since the production fix lives in the project's source tree (documented in the body `## Files` section). See "Artifacts directory" below for when to use the artifact directory (repro repos, crash logs, screenshots).
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.

### Evidence-readiness — reproduction is the floor

A bug without a reproducible failure path is exploratory until reproduction is captured. The same evidence-readiness rule that governs `task` authoring applies — binding shape lives in `./spike-before-task.md`: five evidence categories (reproduce command, code coordinates, data flow, baseline, test fixture) expected by the time the bug is `pending`; reproduction is the strongest signal among them. When two or more are empty the parent issue family is `spike` (PoC reproduction repo) or `research`, not `bug`.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set it when this bug descends from another issue: most commonly a `task` whose work surfaced the regression, or a sibling `bug` whose investigation spun this one off. Cross-type within the issue family (`task` / `bug` / `spike` / `research`) is allowed.
- **Aggregation parent (umbrella)** — set it to an `umbrella/<id>-<slug>` when this bug is one of several children grouped under an umbrella for shared narrative. See `./umbrella-authoring.md` for when to create an umbrella vs. when not to.

The parent file (issue or umbrella) is the agreed home for **narrative shared across siblings**. Record that narrative in the parent's `## Log`, not duplicated in each child. When a child `## Resume` or `## Log` entry depends on a parent decision, inline-cite the parent path in the child entry per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative` so a session reading the child file alone discovers the parent.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Bug-specific notes:

- `complete` means the regression test passes (unit tests green) and the fix is in.
- `cycle:` bumps on `failing → pending` next-cycle defers.
- Required body sections for the `complete` preflight: `## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`.

## Body shape

**Required:**

- `## Description` — what's broken and why the fix matters. State the observed behavior and the expected behavior.
- `## Files` — action / path / change table. Lists production source paths the fix writes or modifies, plus any artifact paths under `artifacts/bug/<id>-<slug>/` when the task uses an artifact directory.
- `## Unit Test Strategy` — regression test scenarios + isolation strategy + test file paths. The bug must end with a test that fails before the fix and passes after.
- `## Acceptance Criteria` — checklist. AC source: **reproduction scenario + fixed criteria** (the regression test pinning the expected behavior). The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts this task consumes or provides, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`).
- `## Resume` — current-state snapshot for the next session: current approach, current blocker, open questions, next step. Freely rewritten as work progresses. Strongly recommended while the bug is non-terminal (any status other than `complete` / `discarded`). See `./issue-body.md#resume`.
- `## Log` — append-only narrative of meaningful events (decision pivots, blocker resolutions, approach changes worth remembering). Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A bug task may have a sibling artifact directory at `<project-root>/artifacts/bug/<id>-<slug>/` when reproduction or evidence is itself worth keeping — minimal repro repos, crash logs, screenshots, traces:

```
<project-root>/
  a4/bug/<id>-<slug>.md             # task markdown — type: bug
  artifacts/bug/<id>-<slug>/        # repro, logs, screenshots (opt-in)
```

Optional — the production fix lives in the project's source tree (documented in body `## Files`), not here. Use the artifact directory only when reproduction artifacts have lasting value (a hard-to-reproduce data file, a heap dump that anchors the regression test). Frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed bug tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions for the artifact directory — per-type expectations, the `artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in `./artifacts.md` and apply to `type: bug` as written there.

## Common mistakes (bug-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/bug/` must declare `type: bug`. Mismatched declarations are a folder-routing error and should be re-located.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Production source belongs in the body `## Files` section.

## Don't (bug-specific)

- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a task stays enqueued or moves forward / out.
- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded` is the writer's job.
- **Don't ship a bug fix without a regression test.** The `## Unit Test Strategy` must include a scenario that pins the expected behavior; closing the task without it is the most common way the same bug returns.
- **Don't author a different issue family here.** Move tasks to `a4/task/`, spikes to `a4/spike/`, and research to `a4/research/` so the matching authoring contract applies.
