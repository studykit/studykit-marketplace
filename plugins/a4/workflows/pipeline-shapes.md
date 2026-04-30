# Pipeline Shapes — Full, Reverse, Minimal

> **Audience:** Skill runtime — LLMs executing a4 skills (and contributors authoring skills). Defines cross-skill workflow contracts (modes, shapes, iterate, wiki-authorship). Workspace authors editing `<project-root>/a4/**/*.md` should read `../authoring/` instead. Plugin internals (hooks, cascade implementation) live in `../dev/`.

The a4 pipeline is not one shape. Three named shapes describe how a workspace flows from intent to shipped code, and one named **no-shape** state describes when no pipeline runs at all. Each constituent skill that behaves differently across shapes cites this document; skills with shape-independent behavior do not.

Companion to:
- [`skill-modes.md`](./skill-modes.md) — interactive vs autonomous, forward vs reverse axes for individual skills.
- [`wiki-authorship.md`](./wiki-authorship.md) — who can write each wiki page; cross-stage feedback policy.
- [`../authoring/frontmatter-universals.md`](../authoring/frontmatter-universals.md) — universal frontmatter rules.
- [`../authoring/<type>-authoring.md`](../authoring/) — per-type field tables and lifecycles.

## Why name the shapes

Most a4 documentation describes the **Full forward** pipeline (`usecase → domain → arch → bootstrap → roadmap → run`). In practice the pipeline runs in at least three distinct shapes:

- A new project starting from a vague idea — the canonical Full forward.
- A brownfield project being reverse-engineered into UCs from existing code.
- A single change (bug fix, small feature, spike) that does not justify the full upstream wiki.

Treating Full as the only shape forces brownfield and one-off work into routing notes scattered across `compass`, `auto-bootstrap`, and `task`. Naming the shapes makes the choice **first-class**: the entry skill is named, the required wiki pages are named, and the constituent skills can branch on shape explicitly instead of inferring it.

## The shape determinant

The single condition that decides whether *any* shape applies is **the presence of `a4/bootstrap.md`**.

`/a4:run` requires `bootstrap.md` for Launch & Verify and halts to compass when it is absent. Every shape — Full, Reverse-then-forward, Minimal — therefore terminates in `/a4:run` and requires `bootstrap.md` somewhere in the path. If `bootstrap.md` does not exist and the user has only written specs, research artifacts, sparks, or hand-edited wiki pages, **no shape applies** — see "No shape" below.

What `bootstrap.md` does **not** depend on:

- It is not specific to greenfield. Brownfield projects produce `bootstrap.md` via `/a4:auto-bootstrap` Step 1 incremental mode (existing code → identify what's already present, set up only what's missing).
- It is not specific to UC-driven projects. UC-less projects produce `bootstrap.md` from a minimal architecture sketch or directly from observed project state.

In other words: `bootstrap.md` is the **anchor every shape needs**, independent of project state and AC source.

## Shape 1: Full forward

**Entry.** `/a4:usecase` (interactive) on a fresh idea, vague intent, or new feature scope.

**Required wiki path.** `usecase → domain → architecture → bootstrap → roadmap` (each successive page authored after the previous one is finalized).

**Required issue path.** `usecase/<id>-<slug>.md` (one or more) → `task/<id>-<slug>.md` (UC-driven batch produced by `/a4:roadmap`).

**Acceptance Criteria source.** Each task's `implements: usecase/<id>-<slug>` resolves to that UC's `## Flow` / `## Validation` / `## Error Handling` sections. `/a4:run` Step 4b ships **per UC**; multiple tasks shipping their target UC's full Flow flip the UC `implementing → shipped`.

**When this shape fits.** Greenfield projects, large new features in any project, and any work where upstream wiki investment pays back across multiple tasks.

## Shape 2: Reverse-engineer

**Entry.** `/a4:auto-usecase` against an existing codebase, idea seed, or brainstorm input.

**Two sub-variants.**

- **Reverse-only.** `/a4:auto-usecase` produces `context.md` / `actors.md` / `domain.md` / per-UC files at `status: draft`; user reviews via `/a4:usecase iterate`. Stops there. Output is a wiki snapshot of the existing system, no implementation runs. `bootstrap.md` may or may not exist; if absent, this is technically a No-shape extension since `/a4:run` never runs (see "No shape").
- **Reverse-then-forward.** Same start, then proceeds into Full forward from `domain` or `arch` onward — the extracted UCs become input for the canonical pipeline. `bootstrap.md` produced via `/a4:auto-bootstrap` incremental against the existing codebase.

**Acceptance Criteria source.** Same as Full once forward stages run (UC-derived).

**When this shape fits.** Brownfield projects where the user wants the wiki to reflect the existing system before adding to it. Reverse-only when the goal is documentation; Reverse-then-forward when the goal is to extend an existing system with new features grounded in the recovered understanding.

## Shape 3: Minimal

**Entry.** One of `/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research`. No UC, domain, or architecture authoring required.

**Required wiki path.** `bootstrap.md` only. `domain.md`, `architecture.md`, `usecase/*.md`, `roadmap.md` are all skippable.

**Required issue path.** `<type>/<id>-<slug>.md` (under one of `a4/task/`, `a4/bug/`, `a4/spike/`, `a4/research/`) → `/a4:run`.

**Acceptance Criteria source.** Set by task family, mirroring the Jira-issue model that the per-family authoring skills are built on:

| Family | AC source |
|---|---|
| `task` + `implements: [usecase/...]` | UC's `## Flow` / `## Validation` / `## Error Handling` (this is Full-shape AC reused inside Minimal) |
| `task` + `spec: [spec/...]` | spec's `## Specification` body + the relevant `architecture.md` section (the canonical Minimal-shape variant for non-UC tasks) |
| `task` with neither | Smell — `/a4:task` Step 2 asks the user where AC will be drawn from, or downgrades to `spike` |
| `bug` | The bug description in the task body itself (regression test pins the expected behavior) |
| `spike` | The hypothesis stated in the task body itself |
| `research` | The body itself is the deliverable; `/a4:research-review` is the quality pass before downstream consumption |

`/a4:run` Step 4b ships **per task** when `task.implements:` is empty (no UC to ship); when `task.implements:` is non-empty, it falls back to per-UC ship as in Full shape. The branching is `task.implements:`-driven, not invocation-driven.

**When this shape fits.** Single bug fixes, spec-justified one-off features, exploration spikes. Common in brownfield projects where the user does not want to retrofit the full wiki for a small change.

## Cross-cutting concerns

### specs (`/a4:spec`)

specs are **orthogonal to shape**. They are produced and consumed across all shapes, with two production channels and two consumption channels:

| Channel | Where | Most common shape |
|---|---|---|
| **Production (primary)** | `/a4:arch` authoring — heavy stack / framework / persistence / auth / integration / test-strategy choices. `arch/SKILL.md` Step 1 explicitly nudges users toward `/a4:research` → `/a4:spec` for non-trivial choices. | Full (arch is Full-only) |
| **Production (secondary)** | `/a4:spec` invoked standalone at any time, in any shape, in any workspace state — including before any pipeline runs. | Any (including No shape) |
| **Consumption (primary)** | `architecture.md` `## Change Logs` bullet linking `[spec/N-...](spec/N-...md)` records why an architecture change happened. | Full |
| **Consumption (secondary)** | `task.spec: spec/N-...` makes a spec the AC source for a non-UC task. | Minimal (canonical), Full (occasional) |

**Trigger conditions** for writing a spec (independent of shape):

1. Two or more viable options with a non-trivial trade-off.
2. The "why" of the choice is not recoverable from the resulting code.
3. The decision could plausibly be revisited later — superseded chains preserve the path not taken.

**When to cite an existing spec.** specs are written once and cited many times. Each citation site falls into one of two categories:

*Mandatory* (the system requires the citation to function correctly):

- `architecture.md` `## Change Logs` bullet `[spec/N-...](spec/N-....md)` whenever an arch section is changed by a spec. Per [`body-conventions.md`](./body-conventions.md) change-log rules.
- `task.spec: [spec/N-...]` frontmatter for Minimal-shape `type: task` tasks grounded in a spec rather than a UC. `/a4:run` Step 4b reads the spec's `## Specification` body plus the cited `architecture.md` section as AC source.
- A successor spec's `supersedes: [spec/N]` chain when a new decision invalidates an old one. The chain preserves history; both files remain on disk and the older spec flips to `superseded` via cascade.
- Other wiki pages' `## Change Logs` (`domain.md`, `nfr.md`, `context.md`) when those pages' changes were driven by a spec — same bullet pattern as architecture.md.

*Optional* (the citation adds clarity but is not required):

- Task body prose (`## Description`, plus open questions captured inside `## Description` or `## Change Logs`) — explain why this task takes a particular approach, even when `spec:` is not set.
- Review item body — clarify what decision a `kind: question` is asking about or what decision a `kind: finding` is violating.
- Research tasks (`a4/research/<id>-<slug>.md`) — the task body's conclusion can forward-point to a spec that fixed its outcome via inline markdown links.

**Common omissions** that erode spec value:

- Writing a spec but not adding the `architecture.md` `## Change Logs` bullet when arch was driven by it. The drift detector may eventually catch this; preferring to add the bullet in the same session avoids the drift entry.
- Minimal-shape `type: task` task with no UC and no spec — `/a4:task` Step 2 flags as smell. The fix is usually to write a short spec first, then cite it via `spec:`.
- Reversing a decision without an explicit `superseded by` chain. Both specs end up live and ambiguous about which is current.

**Anti-patterns** (do not write a spec for these):

- Routine implementation choices (variable naming, file layout).
- Decisions already determined by the framework or platform.
- Post-hoc justification — specs capture the trade-off at decision time, not after the fact.
- Multiple decisions in one file — one decision per file (Nygard 1:1 rule).

specs do not have a shape entry of their own. `/a4:spec` is shape-independent — it always writes the same spec file regardless of which shape (if any) is in flight.

## No shape

When `bootstrap.md` does not exist, no pipeline shape applies. The workspace may still be active — the user may be writing specs, research tasks, sparks, or hand-editing wiki pages — but `/a4:run` cannot execute and no task → ship flow is in motion.

This is a normal state, not an error. Workspaces in this state typically use:

- `/a4:spec` — record specs standalone before any implementation work.
- `/a4:research` — investigate options or topics, producing `a4/research/<id>-<slug>.md`.
- `/a4:research-review` — audit a research task for source quality and bias.
- `/a4:spark-brainstorm` — capture ideas before they take shape.
- Direct wiki edits on `context.md` / `domain.md` for purely descriptive purposes.

A No-shape workspace becomes a shaped workspace the moment `bootstrap.md` is created — typically by `/a4:auto-bootstrap` (which itself requires `architecture.md`, dragging the workspace into Full or Reverse-then-forward) or by direct authoring (Minimal).

`compass` does **not** prompt the user to pick "no shape" explicitly. The Step 2.0 catalog already exposes ideation and standalone skills as fall-throughs; a workspace lacking `bootstrap.md` and choosing one of those skills is in No-shape state by definition.

## Shape detection

For tools and skills that need to know which shape is running:

| Signal | Implies |
|---|---|
| `bootstrap.md` absent | No shape |
| `bootstrap.md` present + `usecase/*.md` absent | Minimal (entry was one of `/a4:task`, `/a4:bug`, `/a4:spike`, `/a4:research`) |
| `bootstrap.md` present + `usecase/*.md` present + `domain.md` and `architecture.md` present | Full (or Reverse-then-forward — the two are indistinguishable from state alone) |
| `usecase/*.md` present + every UC has `source: auto-usecase` frontmatter | Reverse start (could still be Reverse-only or Reverse-then-forward) |

Shape is not stored as a workspace flag. Skills that branch on it derive shape from the current state at invocation time. This keeps shape decisions reversible: a workspace can grow from Minimal into Full by adding upstream wiki pages, or from Reverse-only into Reverse-then-forward by continuing into the forward stages.

## Skills that cite this document

Two skills branch on shape and therefore cite this document:

- **`auto-bootstrap`** — Step 1 Codebase Assessment scope is shape-aware: Full requires architecture.md as the source of truth; Minimal may have no architecture.md and works directly from the existing codebase. The fresh / incremental branch is project-state-driven; the scope-of-work branch is shape-driven.
- **`run`** — Step 4b ship-review unit varies by shape: per-UC when tasks declare `implements:` (Full or Minimal-task-with-UC), per-task when `task.implements:` is empty (Minimal-spec / spike / bug). Branching is `task.implements:`-driven, which is the shape signal at task level.

Skills that **do not** cite this document, by design:

- `usecase`, `domain`, `arch`, `roadmap` — Full-only stages. Shape is determined by the fact of their invocation; no internal branching needed.
- `auto-usecase` — the Reverse entry. Shape is determined by invocation; no internal branching.
- `task` — itself the Minimal entry. Always Jira-issue-modeled regardless of any other shape activity in the workspace.
- `spec` — cross-cutting; shape-independent.
- `compass` — uses this reference at the **Step 2.0 catalog level** (entry routing) rather than as an internal branch citation.

## Reading order

When introducing a new shape, removing one, or changing how an existing shape's required wiki / AC source works, read this document **before** SKILL.md edits. This is the "which path through the pipeline is in flight" reference; `skill-modes.md` is the "who decides vs who verifies" reference; `wiki-authorship.md` is the "who can write what" reference. The three are peer companions in the references hierarchy.
