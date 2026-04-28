# a4 — research task authoring

A research task at `a4/task/research/<id>-<slug>.md` is a **time-boxed investigation** of a technical topic or comparison of alternatives. The body itself is the deliverable — sources consulted, findings, options. No production code is produced; downstream specs or feature tasks may cite the research as input via `related:` or via standard markdown body links.

Lifecycle is identical across task kinds (`feature` / `bug` / `spike` / `research`).

Companion to [`./frontmatter-schema.md §Task`](./frontmatter-schema.md), `./body-conventions.md`.

## When a research task is warranted

A research task is the right slot when:

- The next step is **evidence-gathering**, not coding — the user needs to understand a topic before committing to a shape.
- The output should be **citable** by a later spec, feature task, or design conversation.
- The investigation has a **bounded scope** — a question, a topic, or a fixed set of options to compare.

If the user is already converging on a shape and only needs to capture rationale, that is a `spec` (with optional `<decision-log>` entries), not a research task. If the work is exploratory PoC code rather than written investigation, that is a `kind: spike` task with the `spike/<id>-<slug>/` sidecar.

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
spec: []                             # specs whose open question triggered this research
related: []                          # catchall — e.g., other research tasks on adjacent topics
files: []                            # typically empty; the body is the deliverable
cycle: 1
labels: []                           # free-form tags
milestone: <optional>
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

- `title` is required and must not be a placeholder; the writer rejects `<title>`-shaped strings.
- `kind: research` is fixed for files under `a4/task/research/`. Every task must declare the kind explicitly.
- `mode:` is required for research tasks. `comparative` for option-comparison investigations; `single` for a flat topic / question.
- `options:` is required when `mode: comparative` — list the option names that the body's `<options>` section will cover, one subsection per option.
- `implements:` is **usually empty** — research is investigation, not delivery. Populate only if the research is scoped to a specific UC's open question.
- `spec:` is populated when the research was triggered by a spec's `<open-questions>` or `<rejected-alternatives>` discussion.
- `files:` is typically empty; research output lives entirely in the task body. Populate only when the investigation produced ancillary artifacts under the project tree (data files, evaluation scripts).
- `cycle` starts at `1`; bumped on `failing → pending` next-cycle defers.
- `implemented_by:` is **not** a task field — it is a UC reverse-link written by `refresh_implemented_by.py`. Do not put it on a task.

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

1. Required body sections (`<context>`, plus `<options>` for `comparative` mode or `<findings>` for `single` mode) must be present and non-empty.
2. After writing the file, append an explicit `<log>` block recording the post-hoc origin (the writer never logged a `progress → complete` transition for this task):

   ```markdown
   <log>

   - <YYYY-MM-DD> created at status: complete (post-hoc documentation; investigation captured in this conversation)

   </log>
   ```

   This is the **only** case where `<log>` is written directly — every subsequent entry must come from `transition_status.py`.

## Body shape

(Tag form / link form / H1-forbidden are universal — see `./body-conventions.md`.)

**Required:**

- `<context>` — why the research is needed. The specific question or comparison purpose. 1–3 sentences.

**Required by mode (one of these, never both):**

- `<options>` — for `mode: comparative`. One H3 subsection per option name listed in `options:` frontmatter. Each subsection contains:
  - **Sources consulted** — bullet list of URLs, document paths, or explicit search queries.
  - **Key findings** — paragraph(s) with inline citations to the sources.
  - **Raw excerpts** — concrete evidence (quotes, benchmark numbers, API signatures), preferably wrapped in `<details><summary>Raw excerpts</summary>...</details>` so the section folds cleanly.
- `<findings>` — for `mode: single`. The same structure (Sources consulted / Key findings / Raw excerpts) but flat — no per-option split.

**Optional:**

- `<change-logs>` — append-only audit trail when the body is materially edited post-create.
- `<log>` — append-only writer-owned status-transition trail. Never write into `<log>` directly except for the documented post-hoc-`complete` case above.
- `<why-discarded>` — populated by discard. Dated bullet appended when the discard reason deserves narrative capture beyond the `<log>` line.

Unknown kebab-case tags are tolerated.

## Reviewing a research task

Use `/a4:research-review` to walk a structured quality pass over the task body. The reviewer checks source quality, option balance (in comparative mode), claim grounding, bias, completeness, and decision neutrality. Output is advisory; the user accepts, modifies, or dismisses each finding before the task flips to `complete`.

## Citing a research task from a spec or feature

Citations are **soft** — there is no stored-reverse contract. Two paths:

- **From a spec body.** Add a markdown link inside an appropriate spec section (e.g., `<decision-log>` or `<rejected-alternatives>`): `[task/<id>-<slug>](../task/research/<id>-<slug>.md)`. Optionally add the task path to the spec's `related:` frontmatter list for frontmatter-level discoverability.
- **From a feature task body.** Same — link inside `<description>` or `<interface-contracts>` and optionally add to `related:`.

Reverse lookups (which specs cite a research task) are derived on demand via grep / `search.py`; they are not stored on the research task.

## Don't (research-task-specific)

- **Don't put `implemented_by:` on a task.** It is a UC reverse-link, auto-maintained by `refresh_implemented_by.py` from `task.implements:`.
- **Don't use `progress` or `failing` as an initial status.** They are writer-only, produced by transitions.
- **Don't reverse `pending → open`.** Once enqueued, a research task stays enqueued or moves forward / out.
- **Don't omit `kind:` or `mode:`.** Both are required on research tasks.
- **Don't make the decision in the research body.** Research describes evidence; the decision belongs in a spec's `<decision-log>` (or in conversation that converges on a spec). Sentences like "Therefore X is the right choice" violate decision neutrality and should be removed.
- **Don't write a research task as a placeholder for a spec.** If the user has already converged on a shape, capture it as a spec; if the user wants to capture rationale, use the spec's `<decision-log>`.
- **Don't author a `kind: feature` / `spike` / `bug` task here.** Move them to `a4/task/feature/`, `a4/task/spike/`, or `a4/task/bug/` so the matching per-kind authoring contract applies.
