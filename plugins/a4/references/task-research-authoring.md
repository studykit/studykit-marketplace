# a4 — research task authoring

A research task at `a4/task/research/<id>-<slug>.md` is a **time-boxed investigation** of a technical topic or comparison of alternatives. The body itself is the deliverable — sources consulted, findings, options. No production code is produced; downstream specs or feature tasks may cite the research as input via `related:` or via standard markdown body links.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike` / `research`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

## When a research task is warranted

A research task is the right slot when:

- The next step is **evidence-gathering**, not coding — the user needs to understand a topic before committing to a shape.
- The output should be **citable** by a later spec, feature task, or design conversation.
- The investigation has a **bounded scope** — a question, a topic, or a fixed set of options to compare.

If the user is already converging on a shape and only needs to capture rationale, that is a `spec` (with optional `## Decision Log` entries), not a research task. If the work is exploratory PoC code rather than written investigation, that is a `kind: spike` task with an `artifacts/task/spike/<id>-<slug>/` directory.

## Frontmatter contract (do not deviate)

```yaml
---
type: task
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
kind: research
status: open | pending | progress | complete | failing | discarded
mode: comparative | single
options: [name-a, name-b, name-c]   # only when mode: comparative
implements: []                       # usually empty (research is not a deliverable)
depends_on: []                       # other tasks this one needs first
related: []                          # catchall — e.g., other research tasks on adjacent topics
artifacts: []                        # typically empty; if used, paths under artifacts/task/research/<id>-<slug>/
labels: []                           # free-form tags
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: research` is fixed for files under `a4/task/research/`. Every task must declare the kind explicitly.
- `mode:` is required for research tasks. `comparative` for option-comparison investigations; `single` for a flat topic / question.
- `options:` is required when `mode: comparative` — list the option names that the body's `## Options` section will cover, one subsection per option.
- `implements:` is **usually empty** — research is investigation, not delivery. Populate only if the research is scoped to a specific UC's open question.
- `spec:` is **not allowed** on research (a4 v6.0.0). Cite the triggering spec via a markdown link inside `## Context` body prose; the frontmatter forward link is reserved for `feature` and `bug` tasks.
- `artifacts:` is typically empty; research output lives entirely in the task body. Populate only when the investigation produced ancillary artifacts (raw data, evaluation scripts, charts) — paths must point under `artifacts/task/research/<id>-<slug>/...`. Production source paths the research touches do not belong in `artifacts:` (they belong in body links).
- `cycle:` is **not allowed** on research (a4 v6.0.0); investigation work has no implement-loop cycle. A failed research re-attempt does not bump a counter.
- `implemented_by:` is **not** a frontmatter field on any artifact — the UC ↔ task reverse view is derived on demand from `task.implements:`. Do not place an `implemented_by:` field on tasks or UCs.

### Lifecycle and writer ownership

```
open      → discarded | pending | progress
pending   → discarded | progress
progress  → complete | discarded | failing | pending
complete  → discarded | pending
failing   → discarded | pending | progress
discarded → (terminal)
```

Per-status meaning:

- `open` — Backlog. Captured but not yet committed to the work queue.
- `pending` — In the work queue, awaiting an investigator.
- `progress` — Investigation underway (the user, an agent, or a `/a4:run`-driven loop).
- `complete` — Investigation finalized; sources cited, findings written. Downstream callers may now cite this task.
- `failing` — Investigation could not produce usable findings on this iteration (e.g., sources inaccessible, scope mis-framed). Resumed via `failing → progress` or deferred via `failing → pending`.
- `discarded` — Abandoned. Terminal. Reached via an explicit task-discard when the question is no longer relevant.

Writer rules (task-specific):

- **Allowed initial statuses on file create:** `open` (default — backlog), `pending` (queue-fill intent), `complete` (post-hoc documentation; investigation captured in one shot during the same conversation).
- `progress` and `failing` are **writer-only** — never used as initial statuses. The writer produces them as a result of transitions.
- `open → progress` is allowed (e.g., the user starts researching directly without enqueuing first).
- There is **no `pending → open` reverse** — once enqueued, a research task stays enqueued or moves forward / out.

### `complete` initial-status preflight

When the chosen initial status is `complete`, the investigation is asserted to already be captured in the body. Verify before writing:

1. Required sections (`## Context`, plus `## Options` for `comparative` mode or `## Findings` for `single` mode) must be present and non-empty.
2. If you want the post-hoc origin recorded, append a manual bullet to a `## Log` section (the section is optional and hand-maintained):

   ```markdown
   ## Log

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; investigation captured in this conversation)
   ```

   `transition_status.py` does not touch `## Log`; the section is purely an author convenience.

## Body shape

(Heading form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `## Context` — why the research is needed. The specific question or comparison purpose. 1–3 sentences.

**Required by mode (one of these, never both):**

- `## Options` — for `mode: comparative`. One H3 subsection per option name listed in `options:` frontmatter. Each subsection contains:
  - **Sources consulted** — bullet list of URLs, document paths, or explicit search queries.
  - **Key findings** — paragraph(s) with inline citations to the sources.
  - **Raw excerpts** — concrete evidence (quotes, benchmark numbers, API signatures), preferably wrapped in `<details><summary>Raw excerpts</summary>...</details>` so the section folds cleanly.
- `## Findings` — for `mode: single`. The same structure (Sources consulted / Key findings / Raw excerpts) but flat — no per-option split.

**Optional:**

- `## Change Logs` — append-only audit trail when the body is materially edited post-create.
- `## Log` — optional, hand-maintained status-transition narrative. `transition_status.py` does not touch `## Log`; append a bullet by hand if you want the transition recorded in the body.
- `## Why Discarded` — populated by discard. Dated bullet appended when the discard reason deserves narrative capture.

Unknown H2 headings are tolerated.

## Artifacts directory

A research task may have a sibling artifact directory at `<project-root>/artifacts/task/research/<id>-<slug>/` for ancillary artifacts that don't belong in the body — comparison raw data, charts, evaluation scripts, downloaded sources too large or binary to embed:

```
<project-root>/
  a4/task/research/<id>-<slug>.md             # task markdown — kind: research
  artifacts/task/research/<id>-<slug>/        # raw data, scripts, charts (opt-in)
    *.csv *.png *.py ...
```

Research-specific notes:

- The directory is **opt-in**. Most research tasks need none — the body is the deliverable. Add the directory only when raw evidence cited from the body needs to live alongside the task.
- When `artifacts:` is non-empty, every entry must point under `artifacts/task/research/<id>-<slug>/...`. Empty list stays the typical default.
- No archive convention — closed research tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-kind conventions for the artifact directory — per-kind expectations, the `task.artifacts:` artifact-only contract, what to keep vs. drop, ownership of curation, the project-repo (not scratch) status — live in [`task-artifacts.md`](./task-artifacts.md) and apply to `kind: research` as written there.

## Reviewing a research task

Use `/a4:research-review` to walk a structured quality pass over the task body. The reviewer checks source quality, option balance (in comparative mode), claim grounding, bias, completeness, and decision neutrality. Output is advisory; the user accepts, modifies, or dismisses each finding before the task flips to `complete`.

## Citing a research task from a spec or feature

Citations are **soft** — there is no stored-reverse contract. Two paths:

- **From a spec body.** Add a markdown link inside an appropriate spec section (e.g., `## Decision Log` or `## Rejected Alternatives`): `[task/<id>-<slug>](../task/research/<id>-<slug>.md)`. Optionally add the task path to the spec's `related:` frontmatter list for frontmatter-level discoverability.
- **From a feature task body.** Same — link inside `## Description` or `## Interface Contracts` and optionally add to `related:`.

Reverse lookups (which specs cite a research task) are derived on demand via grep / `search.py`; they are not stored on the research task.

## Don't (research-task-specific)

- **Don't put `cycle:` or `spec:` on a research task.** Both are forbidden on `kind: research` (a4 v6.0.0). Cite triggering specs via markdown links in `## Context` body prose.
- **Don't put `implemented_by:` on a task or UC.** The field was retired (a4 v6.0.0); the reverse view of `task.implements:` is computed on demand.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a research task stays enqueued or moves forward / out.
- **Don't omit `kind:` or `mode:`.** Both are required on research tasks.
- **Don't make the decision in the research body.** Research describes evidence; the decision belongs in a spec's `## Decision Log` (or in conversation that converges on a spec). Sentences like "Therefore X is the right choice" violate decision neutrality and should be removed.
- **Don't write a research task as a placeholder for a spec.** If the user has already converged on a shape, capture it as a spec; if the user wants to capture rationale, use the spec's `## Decision Log`.
- **Don't author a `kind: feature` / `spike` / `bug` task here.** Move them to `a4/task/feature/`, `a4/task/spike/`, or `a4/task/bug/` so the matching per-kind authoring contract applies.
