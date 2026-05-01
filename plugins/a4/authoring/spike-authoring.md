# a4 — spike authoring

A spike at `a4/spike/<id>-<slug>.md` is a **time-boxed exploration to unblock a decision** (XP sense). PoC, investigation, benchmark — throwaway code. The accompanying code lives in the spike's artifact directory at `<project-root>/artifacts/spike/<id>-<slug>/`, **outside** the `a4/` workspace. For pure written investigation without throwaway code, use `type: research` instead.

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders that share the same lifecycle but each has its own authoring contract. Cross-family conventions for artifact directories live in `./artifacts.md`.

Companion to `./frontmatter-universals.md`, `./body-conventions.md`.

## Frontmatter contract (do not deviate)

```yaml
---
type: spike
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | pending | progress | complete | failing | discarded
depends_on: []         # list of paths to other tasks
parent:                # optional: an issue (task / bug / spike / research) this spike descends from
related: []            # catchall for cross-references
artifacts: []          # paths under artifacts/spike/<id>-<slug>/ — never project source tree
labels: []             # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `spike` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `pending` \| `progress` \| `complete` \| `failing` \| `discarded` |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this spike descends from, **or** an `umbrella/<id>-<slug>` aggregating this spike with siblings. Cross-type within the issue family is allowed (e.g., a spike spun out of a stuck task: `parent: task/17-search-history`). See the "Parent and shared narrative" note below. |
| `artifacts` | no | list of strings | artifact paths under `artifacts/spike/<id>-<slug>/` (or `artifacts/spike/archive/<id>-<slug>/...` once archived). **Never** point at the project's production source tree — production paths the spike may also touch are documented in the body `## Files` section. |
| `labels` | no | list of strings | free-form tags |
| `created` | yes | date | `YYYY-MM-DD` |
| `updated` | yes | date | `YYYY-MM-DD` |

`implements` / `spec` / `cycle` are not part of the spike schema — declaring them is an error.

- `title` is required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: spike` is fixed for files under `a4/spike/`. There is no `kind:` field — the type *is* the kind.
- `implements:` is **forbidden** on spike — spikes are exploratory, never UC deliverables. If a spike's outcome turns out to validate a UC, author a follow-up `type: task` with `implements: [usecase/<id>-<slug>]` and link the spike from its `## Description` body.
- `spec:` is **forbidden** on spike. Cite the triggering spec from the spike's `## Description` body via a markdown link — the frontmatter forward link is reserved for `type: task` and `type: bug`.
- `cycle:` is **forbidden** on spike; the spike either succeeds, fails (re-attempt without bumping), or is discarded — there is no multi-cycle implement loop for exploratory work.
- `artifacts:` paths must live under `artifacts/spike/<id>-<slug>/...` (or `artifacts/spike/archive/<id>-<slug>/...` after archive). **Never** point at the project's production source tree — production paths the task may *also* touch are documented in the body `## Files` section, not in frontmatter.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set it when this spike was spawned from another issue: typically a `task` whose work hit a question that needed exploration before the task could proceed. Cross-type within the issue family (`task` / `bug` / `spike` / `research`) is allowed.
- **Aggregation parent (umbrella)** — set it to an `umbrella/<id>-<slug>` when this spike is one of several children grouped under an umbrella for shared narrative. See `./umbrella-authoring.md` for when to create an umbrella vs. when not to.

The parent file (issue or umbrella) is the agreed home for **narrative shared across siblings**. Record that narrative in the parent's `## Log`, not duplicated in each child. When a child Log entry depends on a parent decision, inline-cite the parent path in the child entry per `./body-conventions.md#log` so a session reading the child file alone discovers the parent.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four task issue families — see `./task-family-lifecycle.md`.

Spike-specific notes:

- `complete` means the hypothesis was validated.
- No `cycle:` field — `failing` re-attempts do not bump a counter (there is no multi-cycle implement loop for exploratory work).
- `artifacts:` paths must live under `artifacts/spike/<id>-<slug>/` (or `artifacts/spike/archive/<id>-<slug>/` after archive); the preflight existence check uses these paths.
- Required body sections for the `complete` preflight: `## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Description` — the question being explored and why a spike (vs. going straight to a regular task). State the hypothesis and the decision the spike's outcome will inform.
- `## Files` — action / path / change table. Artifact paths under `artifacts/spike/<id>-<slug>/` for files the spike creates; production source paths the spike may probe or temporarily touch may also appear here for reader context. (Frontmatter `artifacts:` is artifact-only.)
- `## Unit Test Strategy` — may be a one-line "validate hypothesis via <method>" (benchmark, integration probe, sample-driven check). The section is still required.
- `## Acceptance Criteria` — checklist. AC source: **hypothesis + expected result, the spike's own body** — what observable outcome proves or refutes the question. The `## Acceptance Criteria` section must exist regardless.

**Optional, emit only when there is content for them:**

- `## Interface Contracts` — contracts the spike consumes or proposes, with markdown links to `architecture.md` sections (e.g., `[architecture#SessionService](../architecture.md#sessionservice)`). May be omitted for self-contained spikes.
- `## Change Logs` — append-only audit trail when the task body is materially edited post-create.
- `## Log` — resume-context surface for a future session: current approach, blockers, decisions that diverge from upstream, open questions, next step. Strongly recommended while the spike is mid-flight (`pending` / `progress` / `failing`). See `./body-conventions.md#log`.
- `## Why Discarded` — populated by discard. Dated bullet (`<YYYY-MM-DD> — <reason text>`) appended when the discard reason deserves narrative capture.

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

Cross-family conventions for the artifact directory — per-type expectations, the `artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in `./artifacts.md` and apply to `type: spike` as written there.

## Common mistakes (spike-specific)

- **Required section missing** (`## Description`, `## Files`, `## Unit Test Strategy`, `## Acceptance Criteria`).
- **Wrong `type:` value or wrong folder.** A file under `a4/spike/` must declare `type: spike`. Mismatched declarations are a folder-routing error and should be re-located.
- **`artifacts:` paths under the project source tree, not under `artifacts/spike/<id>-<slug>/`** — breaks the throwaway contract; production source paths belong in the body `## Files` section.

(Universal body conventions — stray content above the first H2, malformed headings, sections nested inside other sections, H1 in body — are documented in `./body-conventions.md`.)

## Don't (spike-specific)

- **Don't put `implements:`, `cycle:`, or `spec:` on a spike.** All three are forbidden on `type: spike`. Spikes are exploratory; if the outcome warrants UC delivery, author a follow-up `type: task` that declares `implements:` and `spec:` as needed.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a spike stays enqueued or moves forward / out.
- **Don't auto-delete or auto-archive `artifacts/spike/<id>-<slug>/`** on discard. Archiving is a user-driven `git mv`.
- **Don't write production source from a spike.** `artifacts:` paths staying under `artifacts/spike/<id>-<slug>/` is the contract that keeps PoC code throwaway. If the spike's outcome warrants production work, follow up with a `task` (the default issue family).
- **Don't author a different issue family here.** Move tasks to `a4/task/`, bugs to `a4/bug/`, and research to `a4/research/` so the matching authoring contract applies.
