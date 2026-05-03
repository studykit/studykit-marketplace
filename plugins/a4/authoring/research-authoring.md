# a4 — research authoring

A research item at `a4/research/<id>-<slug>.md` is a **time-boxed investigation** of a technical topic or comparison of alternatives. The body itself is the deliverable — sources consulted, findings, options. No production code; downstream specs or tasks may cite via `related:` or markdown body links.

The four issue families (`task`, `bug`, `spike`, `research`) are sibling top-level folders sharing the same lifecycle, each with its own authoring contract. Cross-family conventions for artifact directories: `./artifacts.md`.

Companion to `./frontmatter-issue.md`, `./issue-body.md`.

## When a research task is warranted

A research task is the right slot when:

- The next step is **evidence-gathering**, not coding — the user needs to understand a topic before committing to a shape.
- The output should be **citable** by a later spec, task, or design conversation.
- The investigation has a **bounded scope** — a question, a topic, or a fixed set of options to compare.

If the user is already converging on a shape and only needs to capture rationale, that is a `spec` (with optional `## Decision Log` entries). If the work is exploratory PoC code rather than written investigation, that is a `type: spike` task with an `artifacts/spike/<id>-<slug>/` directory.

## Frontmatter contract (do not deviate)

```yaml
---
type: research
id: <int — globally monotonic across the workspace>
title: "<short, human-readable phrase>"
status: open | queued | progress | holding | complete | failing | discarded
mode: comparative | single
options: [name-a, name-b, name-c]   # only when mode: comparative
depends_on: []                       # other tasks this one needs first
parent:                              # optional: an issue (task / bug / spike / research) this research descends from
related: []                          # catchall — typically the spec(s) or task(s) this research informs
artifacts: []                        # typically empty; if used, paths under artifacts/research/<id>-<slug>/
labels: []                           # free-form tags
---
```

| Field | Required | Type | Values / format |
|-------|----------|------|-----------------|
| `type` | yes | literal | `research` |
| `id` | yes | int | monotonic global integer |
| `title` | yes | string | human-readable |
| `status` | yes | enum | `open` \| `queued` \| `progress` \| `holding` \| `complete` \| `failing` \| `discarded` |
| `mode` | yes | enum | `comparative` \| `single` |
| `options` | conditional | list of strings | option names — required when `mode: comparative`; forbidden when `mode: single` |
| `depends_on` | no | list of paths | other tasks this one needs first |
| `parent` | no | path | An issue-family file (`task` / `bug` / `spike` / `research`) this research descends from, **or** an `umbrella/<id>-<slug>` aggregating this research with siblings. Cross-type within the issue family is allowed. See "Parent and shared narrative" below. |
| `related` | no | list of paths | soft links — typically the spec(s) or task(s) this research informs |
| `artifacts` | no | list of strings | artifact paths under `artifacts/research/<id>-<slug>/` (typically empty — research output lives in the body) |
| `labels` | no | list of strings | free-form tags |


`implements` / `spec` / `cycle` are not part of the research schema — declaring them is an error.

- `title` required and must not be a placeholder; `<title>`-shaped strings are invalid.
- `type: research` is fixed for files under `a4/research/`.
- `id:` see `./frontmatter-issue.md` § `id`.
- `mode:` is required. `comparative` for option-comparison investigations; `single` for a flat topic / question.
- `options:` is required when `mode: comparative` — list option names that the body's `## Options` section will cover, one subsection per option. Forbidden when `mode: single`.
- `implements:` is **forbidden** on research. If scoped to a specific UC's open question, link the UC from `## Context` body prose.
- `spec:` is **forbidden** on research. Cite the triggering spec via backlink inside `## Context` body prose.
- `cycle:` is **forbidden** on research; investigation work has no implement-loop cycle.
- `artifacts:` is typically empty; research output lives entirely in the task body. Populate only when the investigation produced ancillary artifacts (raw data, evaluation scripts, charts) — paths must point under `artifacts/research/<id>-<slug>/...`.

### Parent and shared narrative

`parent:` is optional. Two cases:

- **Derivation parent** — set when this research was scoped from another issue: typically a `task` author who needed an investigation to settle an open question. Cross-type within the issue family allowed.
- **Aggregation parent (umbrella)** — set to `umbrella/<id>-<slug>` when grouped under an umbrella. See `./umbrella-authoring.md`.

The parent file is the agreed home for **narrative shared across siblings**. Record in the parent's `## Log`. When a child entry depends on a parent decision, inline-cite per `./issue-body.md#inline-cross-references-for-cross-cutting-narrative`.

### Lifecycle and writer ownership

Lifecycle, status enum, writer rules, and `complete` initial-status preflight are shared across the four issue families — see `./issue-family-lifecycle.md`.

Research-specific notes:

- `complete` means the investigation is finalized: sources cited, findings written. Downstream callers may now cite this task.
- `failing` typically signals scope mis-framing or inaccessible sources; deferred via `failing → queued` for re-framing.
- No `cycle:` field.
- No `artifacts:` existence check in the `complete` preflight — research output lives in the body.
- Required body sections for the `complete` preflight: `## Context`, plus `## Options` (when `mode: comparative`) or `## Findings` (when `mode: single`).

## Body shape

**Required:**

- `## Context` — why the research is needed. The specific question or comparison purpose. 1–3 sentences.

**Required by mode (one of these, never both):**

- `## Options` — for `mode: comparative`. One H3 subsection per option name listed in `options:` frontmatter. Each subsection contains:
  - **Sources consulted** — bullet list of URLs, document paths, or explicit search queries.
  - **Key findings** — paragraph(s) with inline citations to the sources.
  - **Raw excerpts** — concrete evidence (quotes, benchmark numbers, API signatures), preferably wrapped in `<details><summary>Raw excerpts</summary>...</details>`.
- `## Findings` — for `mode: single`. Same structure (Sources consulted / Key findings / Raw excerpts) but flat — no per-option split.

**Optional:**

- `## Resume` — current-state snapshot. Strongly recommended while non-terminal. See `./issue-body.md#resume`.
- `## Log` — append-only narrative. Do not duplicate `## Resume` content here. See `./issue-body.md#log`.
- `## Why Discarded` — populated on `discarded`. Format: `./issue-body.md` § `## Why Discarded`.

Unknown H2 headings are tolerated.

## Artifacts directory

A research task may have a sibling artifact directory at `<project-root>/artifacts/research/<id>-<slug>/` for ancillary artifacts that don't belong in the body — comparison raw data, charts, evaluation scripts, downloaded sources too large or binary to embed:

```
<project-root>/
  a4/research/<id>-<slug>.md             # task markdown — type: research
  artifacts/research/<id>-<slug>/        # raw data, scripts, charts (opt-in)
    *.csv *.png *.py ...
```

Research-specific notes:

- The directory is **opt-in**. Most research tasks need none — the body is the deliverable. Add only when raw evidence cited from the body needs to live alongside.
- When `artifacts:` is non-empty, every entry must point under `artifacts/research/<id>-<slug>/...`.
- No archive convention — closed research tasks archive their markdown to `a4/archive/` independently; the artifact directory stays in place.

Cross-family conventions live in `./artifacts.md` and apply to `type: research` as written there.

## Reviewing a research task

A structured quality pass walks the task body before it flips to `complete`. The review checks source quality, option balance (in comparative mode), claim grounding, bias, completeness, and decision neutrality. Output is advisory; the user accepts, modifies, or dismisses each finding.

## Citing a research task from a spec or task

Citations are **soft** — there is no stored-reverse contract. Two paths:

- **From a spec body.** Add a backlink inside an appropriate spec section (e.g., `## Decision Log` or `## Rejected Alternatives`): `` `../research/<id>-<slug>.md` ``. Optionally add the path to the spec's `related:` for frontmatter-level discoverability.
- **From a task body.** Same — link inside `## Description` or `## Interface Contracts` and optionally add to `related:`.

Reverse lookups (which specs cite a research task) are derived on demand via grep / `../scripts/search.py`.

## Don't (research-specific)

- **Don't put `implements:`, `cycle:`, or `spec:` on a research task.** All three are forbidden. Cite triggering specs via backlinks in `## Context` body prose; record the implementing UC the same way.
- **Don't make the decision in the research body.** Research describes evidence; the decision belongs in a spec's `## Decision Log` (or in conversation that converges on a spec). Sentences like "Therefore X is the right choice" violate decision neutrality and should be removed.
- **Don't write a research task as a placeholder for a spec.** If the user has already converged on a shape, capture it as a spec; if the user wants to capture rationale, use the spec's `## Decision Log`.
- **Don't author a different issue family here.** Move tasks to `a4/task/`, spikes to `a4/spike/`, and bugs to `a4/bug/`.
