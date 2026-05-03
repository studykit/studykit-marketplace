# a4 — bug authoring

A bug at `a4/bug/<id>-<slug>.md` is a **defect fix** — production code change against expected behavior. Not throwaway.

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders sharing the same lifecycle, each with its own authoring contract. Cross-family conventions for artifact directories: `./artifacts.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: bug
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | queued | progress | holding | complete | failing | discarded
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
| `status` | yes | enum | `open` \| `queued` \| `progress` \| `holding` \| `complete` \| `failing` \| `discarded` |
| `implements` | no | list of paths | use cases delivered (often empty for bug work that does not implement a UC) |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `spec` | no | list of paths | specs governing this task |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this bug descends from, **or** an `umbrella/<id>-<slug>` aggregating this bug with siblings. Cross-type within the issue family is allowed. See "Parent and shared narrative" below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/bug/<id>-<slug>/` (typically empty — repro/logs/screenshots only when worth keeping) |
| `cycle` | no | int | implementation cycle number |
| `labels` | no | list of strings | free-form tags |


- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: bug` is fixed for files under `a4/bug/`. No `kind:` field — the type *is* the kind.
- `id:` see `./frontmatter-issue.md` § `id`.
- `implements:` lists `usecase/<id>-<slug>` paths. Declare when the bug traces to a UC's flow.
- `spec:` lists `spec/<id>-<slug>` paths. Declare when the bug is a regression against a spec's expected behavior.
- `implements:` and `spec:` are **optional and orthogonal** — zero, one, or both. Empty anchors are common for cross-cutting fixes.
- `artifacts:` is artifact-only — paths must point under `artifacts/bug/<id>-<slug>/...`. Typically empty since the production fix lives in the project source tree; git history is authoritative, and the optional body `## Change Plan` may name fix paths as a forward-looking scope fence. See "Artifacts directory" below.
- `cycle` starts at `1`; bumped on `failing → queued` next-cycle defers.

### Evidence-readiness — reproduction is the floor

A bug without a reproducible failure path is exploratory until reproduction is captured. Same evidence-readiness rule as `task` authoring — binding shape: `./spike-before-task.md`. Five evidence categories (reproduce command, code coordinates, data flow, baseline, test fixture) expected by the time the bug is `queued`; reproduction is the strongest signal. When two or more are empty the parent issue family is `spike` (PoC reproduction repo) or `research`, not `bug`.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set when this bug descends from another issue: most commonly a `task` whose work surfaced the regression, or a sibling `bug` whose investigation spun this one off. Cross-type within the issue family allowed.
- **Aggregation parent (umbrella)** — set to `umbrella/<id>-<slug>` when this bug is one of several children grouped under an umbrella for shared narrative. See `./umbrella-authoring.md`.

The parent file is the agreed home for **narrative shared across siblings**. Record in the parent's `## Log`, not duplicated in each child. When a child entry depends on a parent decision, inline-cite the parent path per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Bug-specific notes:

- `complete` means the regression test passes (unit tests green) and the fix is in.
- `cycle:` bumps on `failing → queued` next-cycle defers.
- Required body sections for the `complete` preflight: `## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`. (`## Change Plan` is optional.)

## Body shape

**Required:**

- `## Description` — what's broken and why the fix matters. State observed vs. expected behavior.
- `## Unit Test Strategy` — regression test scenarios + isolation strategy + test file paths. The bug must end with a test that fails before the fix and passes after.
- `## Acceptance Criteria` — checklist. AC source: **reproduction scenario + fixed criteria** (the regression test pinning expected behavior). The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Change Plan` — forward-looking scope fence. Action / path / change table (or bullet list) listing production source paths the fix plans to write or modify, plus any artifact paths under `artifacts/bug/<id>-<slug>/`. Distinct from git history (which records changes *after the fact*); records what is *planned* before the fix lands. Useful when the fix spans multiple files or sits next to siblings whose scope must be partitioned. Skip for single-file fixes.
- `## Interface Contracts` — contracts this task consumes or provides, with backlinks to `architecture.md` sections (e.g., `` `../architecture.md#sessionservice` ``).
- `## Resume` — current-state snapshot for the next session. Strongly recommended while non-terminal (any status other than `complete` / `discarded`). See `./issue-body.md#resume`.
- `## Log` — append-only narrative. Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated on `discarded`. Format: `./issue-body.md` § `## Why Discarded`.

Unknown H2 headings are tolerated.

## Artifacts directory (optional)

A bug task may have a sibling artifact directory at `<project-root>/artifacts/bug/<id>-<slug>/` when reproduction or evidence is itself worth keeping — minimal repro repos, crash logs, screenshots, traces:

```
<project-root>/
  a4/bug/<id>-<slug>.md             # task markdown — type: bug
  artifacts/bug/<id>-<slug>/        # repro, logs, screenshots (opt-in)
```

Optional — the production fix lives in the project source tree (recorded by git history; the optional body `## Change Plan` may name it for forward-looking scope-fencing). Use the artifact directory only when reproduction artifacts have lasting value (a hard-to-reproduce data file, a heap dump that anchors the regression test). Frontmatter `artifacts:` lists artifact paths only.

No archive convention — closed bug tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions live in `./artifacts.md` and apply to `type: bug` as written there.

## Common mistakes (bug-specific)

- **Required section missing** (`## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/bug/` must declare `type: bug`. Mismatched declarations are a folder-routing error.
- **Production source paths in frontmatter `artifacts:`** — `artifacts:` is artifact-only. Rely on git history (and the optional body `## Change Plan`).

## Don't (bug-specific)

- **Don't manually flip cascade-driven statuses.** UC `discarded` → task `discarded` is the writer's job.
- **Don't ship a bug fix without a regression test.** The `## Unit Test Strategy` must include a scenario pinning the expected behavior; closing the task without it is the most common way the same bug returns.
- **Don't author a different issue family here.** Move tasks to `a4/task/`, spikes to `a4/spike/`, and research to `a4/research/`.
