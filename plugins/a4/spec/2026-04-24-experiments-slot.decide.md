---
type: decide
pipeline: spark
topic: "Experiments / PoC Slot"
date: 2026-04-24
updated: 2026-04-24
status: final
framework: "analysis-driven"
decision: "Reuse `a4/task/` with a required `kind: feature | spike | bug` enum; PoC code lives at project-root `spike/<task-id>-<slug>/`, outside the `a4/` markdown workspace; closed PoCs are archived by manual `git mv` to `spike/archive/<task-id>-<slug>/`; no new a4 folder, no automation skill"
tags: [a4-pipeline, document-model, a4, experiment, spike, task]
---
# Decision Record: Experiments / PoC Slot

> Source: gap surfaced while reviewing the `a4-redesign` handoff thread — the 2026-04-23_2119 handoff explicitly parked an "Experiments / PoC slot" item, which was never picked up in the subsequent 13 ADR Next Steps nor in the thread-closure handoff. The 2026-04-24 idea-slot ADR resolved item 3 (Inbox slot) from the same parked list and explicitly deferred this item; this ADR resolves it.

## Context

The 2026-04-23_2119 handoff parked three items as "not dropped, but out of scope for that thread":

> 4. **Experiments / PoC slot.** Placeholder — naming (`<topic>.<stage>.experiment-<label>.md` vs. running log `<topic>.experiments.md`), location, and how it interacts with `reflected_files`. Parked explicitly.

The original framing predates the 2026-04-23 wiki+issues redesign. `reflected_files` no longer exists, stage-stamped filenames are gone, and the workspace now consists of flat wiki pages plus five issue-type folders (`usecase/`, `task/`, `review/`, `decision/`, `idea/`). The question reframes to: **in the current model, where do PoC code, spike investigations, and time-boxed experiments fit?**

The triggering pain is real but bounded:

- A spike (XP/agile sense — time-boxed exploration to unblock a decision) produces *throwaway* code plus a short writeup. The code is not production; the writeup is the deliverable.
- A PoC (proof-of-concept) is similarly throwaway code that demonstrates feasibility before a feature task is committed to.
- Investigation notes ("I tried X, here's what happened") have only a markdown component but the same lifecycle posture: provisional, decision-supporting, eventually archived or absorbed.

None of these have an obviously correct home. `task/` is the closest existing slot but its body is markdown-only, and `a4/` has been a pure markdown workspace since the redesign.

## Success Criteria

Ranked:

1. **Workspace contract preserved** — `a4/` stays a pure markdown documentation workspace. PoC code (`.py`, `.ts`, `.json`, scripts, sample data) does not live inside the `a4/` tree.
2. **No new a4 issue type** unless the boundary with `task/` is sharp enough to justify it. Three confirmed uses (PoC, spike, investigation) all share the same lifecycle posture — distinguishable but not different enough to warrant a new folder, especially when `task/` already accepts spike-shaped work.
3. **Lightweight code-tracking** — task `files:` field already records "source paths the task writes or modifies"; reuse it for spike/PoC code paths instead of inventing a parallel field.
4. **Cleanup discipline** — closed spike work should not leave PoC directories scattered across the repo. A single archive convention (move `spike/<id>-<slug>` → `spike/archive/<id>-<slug>`) keeps cleanup discoverable without automation.
5. **No premature tooling** — match the idea-slot precedent: capture-skill or promote-skill only when manual cost surfaces as actual pain.

## Decision

### No new a4 folder. Extend `a4/task/` with a `kind` field

`a4/task/` already holds executable work units (Jira "task" semantics). Spike and bug fixes are *kinds* of task — same lifecycle (`pending | implementing | complete | failing`), same id space, same body shape — so they reuse the slot rather than spawn new ones. The distinction is captured by adding a required `kind:` field:

```yaml
---
id: 12
title: "JWT rotation: try Auth0 vs PyJWT"
kind: spike            # NEW. Required. Enum: feature | spike | bug
status: pending
created: 2026-04-24
updated: 2026-04-24
---
```

`kind` enum (closed, three values):

| Value | Meaning |
|-------|---------|
| `feature` | Regular implementation work — new functionality, extension, refactor. The default case. |
| `spike` | Time-boxed exploration to unblock a decision (XP sense). Throwaway code expected. PoC, investigation, benchmark. |
| `bug` | Defect fix. Production code change, not throwaway. |

`kind` is **required** on every task. There is no implicit default — any task without `kind:` fails validation. Rationale: distinguishing implicit-default from spike-or-bug at read time would require body inspection. Required field is cheap to author (`kind: feature` for the common case) and free at lookup.

### PoC code lives outside `a4/`, at project-root `spike/<task-id>-<slug>/`

For tasks with `kind: spike`, accompanying PoC code goes in a sibling top-level directory:

```
<project-root>/
  a4/
    task/
      12-jwt-rotation-poc.md          # task markdown (kind: spike)
  spike/                              # NEW top-level convention
    12-jwt-rotation-poc/
      try1.py
      benchmark.json
      notes.md
      sample_payload.json
```

Path matches the task by `<id>-<slug>` for trivial round-trip lookup. Task's `files:` field records the actual file paths inside `spike/<id>-<slug>/`:

```yaml
files:
  - spike/12-jwt-rotation-poc/try1.py
  - spike/12-jwt-rotation-poc/benchmark.json
```

The `spike/` directory:

- **Lives outside `a4/`** so the markdown-only contract of the workspace is preserved. `a4/` validators, INDEX, drift-detector are unaffected.
- **Is a regular project directory** — same git treatment as any other source folder. Not gitignored (PoC history has value).
- **Is opt-in** — projects without spike tasks have no `spike/` directory. The convention activates only when a `kind: spike` task is created.

`feature` and `bug` tasks have no equivalent sidecar; their `files:` field points at production source paths under the project's normal source tree.

### Archive convention — manual `git mv` to `spike/archive/<task-id>-<slug>/`

When a spike task transitions to a terminal state (`complete` or `failing`), the user manually moves the spike directory:

```
spike/
  archive/
    12-jwt-rotation-poc/      # moved from spike/12-jwt-rotation-poc/
      try1.py
      benchmark.json
      notes.md
      sample_payload.json
  17-cache-eviction-spike/    # still active
    ...
```

After the move, the user updates the task's `files:` paths to point at the new location:

```yaml
files:
  - spike/archive/12-jwt-rotation-poc/try1.py
  - spike/archive/12-jwt-rotation-poc/benchmark.json
```

**Why archive instead of delete?**

- Spike outcomes inform later decisions; the original code is the receipt. A test passed because of one specific JWT library version — six months later, regenerating that proof from the writeup alone is expensive.
- Disk cost is negligible (kilobytes per spike, typically).
- `git rm`-ing PoC code is irreversible in working memory; archiving is reversible, the user can promote a snippet back to production later.

**Why manual, not a skill?**

Same logic as the idea-slot deferral of `/a4:idea-promote`: the operation is mechanical (one `git mv`, four-or-so `files:` path edits) and infrequent. A skill earns its place when the manual pattern repeats often enough that the user notices the friction. If/when that surfaces, `/a4:spike-archive <task-id>` can be written then.

**Why nest `archive/` under `spike/` rather than at project root?**

Self-contained. The whole "experiments" footprint is one directory. A future `archive/` at project root would have to define a multi-tenant policy (what else lives there? feature flags? old configs?). Out of scope.

### `kind` interaction with other task fields

| Field | `kind: feature` | `kind: spike` | `kind: bug` |
|-------|-----------------|---------------|-------------|
| `implements` | use case path(s) — the task delivers them | typically empty (spikes don't implement use cases) | optional — bug may relate to a use case |
| `files` | production source paths | `spike/<id>-<slug>/...` paths (or `spike/archive/...` after archive) | production source paths being patched |
| `cycle` | implementation cycle number | not meaningful | implementation cycle number |
| `milestone` | yes | not typically | yes |
| `justified_by` | decisions justifying scope | decisions the spike is unblocking | decision authorizing the fix (rare) |

These are **conventions**, not validator-enforced. The validator only checks `kind` is one of the three enum values when present, and that it is present at all (required).

### Workspace boundary clarification

The 2026-04-23 ADR fixed `a4/` as the workspace's documentation root with a single-topic-per-workspace assumption. The `spike/` directory is a *project*-root sibling, deliberately outside that contract. To make this explicit:

- **`a4/`** = markdown documentation workspace (wiki + issue tracker). Validators, INDEX, drift, dataview all operate within this tree.
- **`spike/`** = project-root code/data sidecar for spike tasks. No validators apply. Cross-referenced from `a4/task/<id>-<slug>.md` only via the task's `files:` field.
- **Same project, different contracts.** A task in `a4/task/` can refer to files outside `a4/` (it always could — `files:` paths typically point at the project's source tree).

## Rejected Alternatives

| Option | Reason |
|--------|--------|
| **New `a4/experiment/` or `a4/spike/` folder** | The boundary with `task/` is not sharp. Spike lifecycle (`pending → implementing → complete/failing`) is identical to task lifecycle. Spike body shape (one-liner title + short rationale + result) fits the task body shape. Spike id space and spike id allocation can be the workspace global counter without modification. The only thing different is "this task happens to produce throwaway code." That is one frontmatter field, not a new file type. |
| **`a4/experiment/<id>-<slug>/` folder containing markdown + PoC code** | Breaks the markdown-only contract of the `a4/` workspace. Validators, INDEX-refresh, drift, dataview would all have to learn to skip non-markdown files. The contract erosion is permanent and load-bearing for several tools. |
| **PoC code at `a4/task/<id>-<slug>/poc/` (sidecar inside task folder)** | Requires per-task folder promotion (some tasks become folders, some stay files) — asymmetric. Same markdown-contract erosion as the above option. Also: would force ALL task files to migrate to folder form for consistency, which is a much larger change. |
| **PoC code at project-root `experiments/<id>-<slug>/` (different folder name)** | "Experiments" connotes ongoing measurement and benchmark suites; spike is the more common term in agile vocabulary for time-boxed throwaway exploration. `spike/` matches the kind enum value verbatim, which makes the convention discoverable from the task frontmatter alone. |
| **PoC code free-form (user picks any path; only `files:` records it)** | Eliminates discoverability — given a task id, finding its PoC code requires reading the markdown. Fixed `spike/<id>-<slug>/` convention enables tooling (current and future) to operate on spike artifacts directly. |
| **PoC code outside the repo entirely** (separate workspace, scratch directory) | Loses git history of PoC iterations; loses cross-machine portability; loses the ability to attach PoC results to PRs/issues; violates the user's explicit "코드/데이터 파일의 위치는 워크스페이스 안" preference (where workspace = project repo). |
| **Optional `kind` field with no value implying "feature"** | Distinguishing "implicitly feature" from "explicitly spike" requires reading every task's frontmatter to detect absence — same cost as making `kind` required. Required-with-default-typed-by-author is more honest about the schema. Author cost is one extra line per task, validator catches forgetting. |
| **Wider `kind` enum** (e.g., `feature \| story \| chore \| refactor \| spike \| bug`) | YAGNI. Three values cover the actually-distinguished cases (default work, throwaway exploration, defect fix). Wider taxonomy invites bikeshedding ("is this a chore or a refactor?") with no downstream consumer of the distinction. Enum can be widened later without breaking validation. |
| **Auto-archive on `status: complete` transition** (hook-driven `mv`) | Destructive automation. A user may legitimately want PoC files to remain at `spike/<id>-<slug>/` for a few more days while a related decision crystallizes. Manual archive preserves user agency over the `git mv`. |
| **`/a4:spike-new <title>` capture skill** (parallel to `/a4:idea`) | Spike task creation is not a 30-second hot-path the way idea capture is. A spike implies a non-trivial time investment ahead — the cognitive cost of typing frontmatter is dominated by the cost of doing the spike. No friction gap to close yet. |
| **`/a4:spike-archive <task-id>` skill** | Manual archive is one `git mv` plus a few path edits. Skill is deferrable until the manual pattern repeats often enough to be felt as friction. Same precedent as idea-slot's deferred `/a4:idea-promote`. |
| **Add `archived: true` boolean on task instead of moving directory** | Conflates two state machines. The task's lifecycle is already tracked via `status:`; the PoC code's lifecycle is *physical* (where the bytes live). Coupling them via a frontmatter flag invites consistency bugs (status complete + archived false + code still at spike/<id>-<slug>/, or status incomplete + archived true). Physical separation in the filesystem is its own affordance. |
| **Track spike code in a `poc_files:` field separate from `files:`** | `files:` is documented as "source paths the task writes or modifies" — that already covers spike code. Two fields would force readers to check both, with no benefit. Spike-vs-feature distinction is already captured by `kind:`. |
| **Compass surfaces "complete spikes with non-archived PoC" as a cleanup nag** | Useful eventually but premature. Compass currently diagnoses workspace state from `a4/` only; teaching it to inspect `spike/` adds a cross-contract dependency. Add when manual cleanup discipline proves insufficient. |
| **INDEX surfaces "Open spikes" as a separate section** | Spikes are tasks. They appear in the existing "Open issues" section's task row alongside features and bugs. Filtering by `kind:` is a dataview query the user can write inline if needed. A dedicated section would imply spikes deserve special operational attention beyond what `status: pending` already conveys. |

## Next Steps

Sequenced by prerequisite dependency:

- [x] **ADR.** This file.
- [x] **Validator schema.** Add required `kind` enum to `task` Schema in `scripts/validate_frontmatter.py`.
- [x] **Schema doc.** Add `kind` row to Task table in `references/frontmatter-schema.md`; document the workspace boundary and the `spike/` directory convention.
- [x] **README.** Layout diagram annotates `spike/` as a project-root sibling of `a4/`; Wiki-vs-issues bullets gain a "Spike vs. feature task" entry; pointer to this ADR.
- [x] **Version bump.** `marketplace.json` a4 `1.2.0 → 1.3.0` (minor — additive schema field, additive directory convention).

Deliberately deferred (not Next Steps; recorded for future-work surfaces):

- **`/a4:spike-archive <task-id>` skill** — automate the `git mv` + `files:` path rewrite. Add when manual pattern repeats often enough to be noticeable.
- **Compass spike-cleanup surfacing** — diagnose "complete spike with non-archived PoC files" as an alert. Add if manual archive discipline proves insufficient.
- **Existing-task migration tooling** — every existing task (legacy or otherwise) without `kind:` will fail validation after this lands. The `a4-redesign` precedent (legacy data stays as-is; new model applies forward) plus this plugin's own `a4/` using legacy layout means this is intentionally not addressed. If a real workspace with many existing task files needs upgrading, a one-shot `add_kind_feature.py` script can be written then.

## Discussion Log

<details>
<summary>Conversation summary</summary>

**Trigger.** User opened the `experiments-slot` thread immediately after reading the idea-slot handoff, which had recorded "Experiments / PoC slot — Remains parked" as item 4 from the 2026-04-23_2119 list.

**Reframe required.** The original 2026-04-23 framing assumed pre-redesign architecture (stage-stamped filenames, `reflected_files`). Both have been removed. The actual question in the current model: where do PoC code and spike writeups fit alongside `usecase/task/review/decision/idea`?

**Four-question intent capture.** What is "experiment"? (a/b confirmed: PoC code + investigation notes; d=spike needed clarification). Where do results flow? (decision/task/review; archive by user). Sharp enough to need new slot? (No — task with kind:spike branch suffices). Code/data location? (project repo, but workspace boundary needed clarification).

**Workspace definition grounded.** Initial `a4/`-vs-repo ambiguity resolved in user's framing: "워크스페이스 = a4/ 폴더 + source 코드 = 프로젝트 경계." This confirmed PoC code lives in the *project repo* (not necessarily inside `a4/`), preserving `a4/` as a markdown-only documentation workspace.

**Three implementation choices made.** (1) `kind` enum on task. Initial proposal `spike` only; user added `bug`; later required adding `feature` for the regular case (so `kind` becomes required, not optional). (2) `spike/<id>-<slug>/` at project root for PoC code (option b1 — self-contained archive nested under spike/). (3) Manual archive via `git mv`, no skill (option c1 — same precedent as idea-slot's deferred `/a4:idea-promote`).

**`feature` chosen** over `general` and `default` for the regular-task kind value — Jira/agile convention familiar, semantically peer to `spike` and `bug`.

</details>
