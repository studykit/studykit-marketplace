# a4 — spike authoring

A spike at `a4/spike/<id>-<slug>.md` is a **time-boxed exploration to unblock a decision** (XP sense). PoC, investigation, benchmark — throwaway code. Accompanying code lives in the spike's artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/`, **outside** the `a4/` workspace. For pure written investigation without throwaway code, use `type: research`.

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders sharing the same lifecycle, each with its own authoring contract. Cross-family conventions for artifact directories: `./artifacts.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: spike
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | queued | progress | holding | complete | failing | discarded
depends_on: []         # list of paths to other tasks
parent:                # optional: an issue (task / bug / spike / research) this spike descends from
related: []            # catchall for cross-references
artifacts: []          # paths under artifacts/spike/<id>-<slug>/ — never project source tree
labels: []             # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spike` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `queued` \| `progress` \| `holding` \| `complete` \| `failing` \| `discarded` |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this spike descends from, **or** an `umbrella/<id>-<slug>` aggregating this spike with siblings. Cross-type within the issue family is allowed (e.g., a spike spun out of a stuck task: `parent: task/17-search-history`). See "Parent and shared narrative" below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/spike/<id>-<slug>/` (or `artifacts/spike/archive/<id>-<slug>/...` once archived). **Never** point at production source — production paths the spike may touch are recorded by git history, and the optional body `## Change Plan` may name them as a forward-looking scope fence. |
| `labels` | no | list of strings | free-form tags |


`implements` / `spec` / `cycle` are not part of the spike schema — declaring them is an error.

- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: spike` is fixed for files under `a4/spike/`. No `kind:` field — the type *is* the kind.
- `id:` see `./frontmatter-issue.md` § `id`.
- `implements:` is **forbidden** on spike — spikes are exploratory, never UC deliverables. If a spike's outcome validates a UC, author a follow-up `type: task` with `implements: [usecase/<id>-<slug>]` and link the spike from its `## Description`.
- `spec:` is **forbidden** on spike. Cite the triggering spec from the spike's `## Description` body via markdown link.
- `cycle:` is **forbidden** on spike; the spike either succeeds, fails (re-attempt without bumping), or is discarded — there is no multi-cycle implement loop for exploratory work.
- `artifacts:` paths must live under `artifacts/spike/<id>-<slug>/...` (or `artifacts/spike/archive/<id>-<slug>/...` after archive). **Never** point at production source.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set when this spike was spawned from another issue: typically a `task` whose work hit a question that needed exploration. Cross-type within the issue family allowed.
- **Aggregation parent (umbrella)** — set to `umbrella/<id>-<slug>` when this spike is one of several children grouped under an umbrella. See `./umbrella-authoring.md`.

The parent file is the agreed home for **narrative shared across siblings**. Record in the parent's `## Log`. When a child entry depends on a parent decision, inline-cite per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Spike-specific notes:

- `complete` means the hypothesis was validated.
- No `cycle:` field — `failing` re-attempts do not bump a counter.
- `artifacts:` paths must live under `artifacts/spike/<id>-<slug>/` (or `artifacts/spike/archive/<id>-<slug>/` after archive); the preflight existence check uses these paths.
- Required body sections for the `complete` preflight: `## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`. (`## Change Plan` is optional.)

## Body shape

**Required:**

- `## Description` — the question being explored and why a spike (vs. a regular task). State the hypothesis and the decision the spike's outcome will inform.
- `## Unit Test Strategy` — may be a one-line "validate hypothesis via <method>" (benchmark, integration probe, sample-driven check). Section still required.
- `## Acceptance Criteria` — checklist. AC source: **hypothesis + expected result, the spike's own body** — what observable outcome proves or refutes the question. Section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Change Plan` — forward-looking scope fence. Action / path / change table (or bullet list) listing artifact paths under `artifacts/spike/<id>-<slug>/` the spike plans to create, plus any production source paths the spike may probe or temporarily touch (for reader context). Distinct from git history; records what is *planned* before exploration begins. Skip when the artifact directory is self-explanatory. (Frontmatter `artifacts:` is artifact-only.)
- `## Interface Contracts` — contracts the spike consumes or proposes, with markdown links to `architecture.md` sections.
- `## Resume` — current-state snapshot for the next session. Strongly recommended while non-terminal. See `./issue-body.md#resume`.
- `## Log` — append-only narrative. Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`).

Unknown H2 headings are tolerated.

## Artifacts directory

For every spike task, accompanying PoC code lives at `<project-root>/artifacts/spike/<id>-<slug>/`, parallel to (not inside) `a4/`:

```
<project-root>/
  a4/spike/<id>-<slug>.md             # task markdown — type: spike
  artifacts/spike/<id>-<slug>/        # PoC code, data, scratch notes
    *.py *.json ...
```

Spike-specific notes:

- The directory is the spike's primary deliverable while exploration is underway. Most active spikes have one.
- When the spike completes (or fails), `git mv` it to `artifacts/spike/archive/<id>-<slug>/` and update `artifacts:` paths to match. The move is **never automated**.

Cross-family conventions live in `./artifacts.md` and apply to `type: spike` as written there.

## Common mistakes (spike-specific)

- **Required section missing** (`## Description`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/spike/` must declare `type: spike`. Mismatched declarations are a folder-routing error.
- **`artifacts:` paths under the project source tree, not under `artifacts/spike/<id>-<slug>/`** — breaks the throwaway contract; production source paths the spike may temporarily touch are recorded by git history (and may be named in the optional body `## Change Plan`).

## Don't (spike-specific)

- **Don't put `implements:`, `cycle:`, or `spec:` on a spike.** All three are forbidden. If the outcome warrants UC delivery, author a follow-up `type: task`.
- **Don't auto-delete or auto-archive `artifacts/spike/<id>-<slug>/`** on discard. Archiving is a user-driven `git mv`.
- **Don't write production source from a spike.** `artifacts:` paths staying under `artifacts/spike/<id>-<slug>/` is the contract that keeps PoC code throwaway. If the outcome warrants production work, follow up with a `task`.
- **Don't author a different issue family here.** Move tasks to `a4/task/`, bugs to `a4/bug/`, and research to `a4/research/`.
