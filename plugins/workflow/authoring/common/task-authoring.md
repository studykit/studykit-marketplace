# Workflow Task Authoring

A workflow task is an **issue-backed unit of regular implementation work**: new functionality, extension, refactor, or other planned code change.

Tasks are stored in the configured issue backend. They are not local Markdown files unless a local projection workflow is explicitly configured.

Companion contracts:

- `./body-conventions.md`
- Issue rules: `./issue-authoring.md`

## Storage role

`task` is stored in the issue backend.

Use canonical issue identity. Do not use local integer ids.

## Required metadata

Represent this metadata structurally when possible. If a field cannot be stored structurally, include the value in the body when the selected authoring files require it.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `task`. Use issue metadata when available. |
| `title` | yes | Short human-readable work summary. |
| `status` | yes | Workflow lifecycle status. |
| `priority` | optional | Workflow priority or field. |
| `tags` | optional | Classification tags. |

## Relationships

Represent relationships structurally when possible. Body representation depends on the selected provider and type authoring files.

| Relationship | Required | Notes |
| --- | --- | --- |
| `implements` | recommended when UC-driven | Use case or requirement this task delivers. |
| `depends_on` | optional | Blocking or ordering dependency. |
| `parent` | optional | Epic or parent issue that coordinates this task. |
| `related` | optional | Non-blocking references useful for implementation. |

## Lifecycle

Recommended semantic lifecycle:

```text
open → queued → progress → done
open → discarded
queued → progress | holding | discarded
progress → holding | failing | done | discarded
holding → queued | progress | discarded
failing → queued | discarded
done → terminal
discarded → terminal
```

Status mapping depends on the configured issue backend.

Status meaning:

- `open` — Captured but not yet ready for execution.
- `queued` — Ready to implement.
- `progress` — Implementation is active.
- `holding` — Paused for external input or sequencing.
- `failing` — Attempt failed and needs rework or reframing.
- `done` — Implementation and verification are complete.
- `discarded` — No longer needed.

`open` is the default initial status for newly authored tasks unless the user explicitly asks to queue it.

## Anchors and scope

A task should usually have at least one acceptance source:

- `implements`: a use case or requirement the task delivers.
- `spec`: a knowledge artifact that defines the implementation contract.
- `parent`: an epic or parent issue that coordinates a batch of work.

Anchorless tasks are allowed for small, obvious changes, but they should pass a smell check:

- If the task implies user-facing behavior with no use case, create or link a use case.
- If the task implies a protocol, schema, API shape, or architectural decision with no spec, create or link a spec.
- If the task is exploratory and evidence is missing, use `spike` or `research` instead.

Do not hide design decisions only in the task body when they should become curated knowledge.

## Parent metadata and shared narrative

Use `parent` for:

- Epic coordination.
- Decomposition from another issue.
- Follow-up work from a spike, bug, research item, or task.

Narrative that affects several children belongs in the parent issue comments or body. A child task should use structured parent metadata when available.

## Granularity

Split a task when it spans:

- Unrelated code areas.
- Independent acceptance criteria.
- Independent test surfaces.
- Work that can be assigned or sequenced independently.

Use dependencies to order split tasks. Use an epic or parent issue when siblings need shared coordination.

## Body shape

Required:

```markdown
## Description

<what and why>

## Unit Test Strategy

<scenarios, isolation strategy, and expected test locations>

## Acceptance Criteria

- <observable done condition>
```

`## Acceptance Criteria` must exist even when the task has metadata links to use cases or specs.

`## Description` must include why the task exists, not only what will change.
State the motivation explicitly for removals, boundary changes, agent
responsibility changes, schema or contract changes, and work that prevents a
known regression.

Use `## Change Plan` for the expected implementation scope. Do not hide the
motivation only in the plan. If the rationale is a long-lived design decision,
create or update the relevant knowledge artifact instead of embedding the full
decision record in the task body.

Acceptance criteria should be grounded in:

- Linked use case flow, validation, and error handling.
- Linked spec specification.
- Linked architecture/domain context.
- Explicit user request when no curated artifact exists yet.

Optional sections:

- `## Change Plan` — forward-looking scope fence naming files, packages, APIs, or migration steps expected to change.
- `## Interface Contracts` — contracts this task consumes or provides.
- `## Resume` — current-state snapshot while mid-flight. See `./body-conventions.md`.
- `## Why Discarded` — reason when discarded. See `./body-conventions.md`.

Unknown Title Case H2 headings are tolerated.

## Evidence-readiness

A queued task should be actionable as a handoff.

Before moving to `queued`, check that the issue body or linked artifacts provide enough evidence for implementation:

- Reproduction or invocation command when relevant.
- Code coordinates or expected implementation area.
- Data flow or API contract when relevant.
- Current baseline behavior.
- Test fixture or test strategy.

If two or more evidence categories are unknown, consider `spike` or `research` instead of `task`.

## Artifacts

Issue-backed tasks usually do not need a local artifact directory.

Use linked external artifacts only when they have evidentiary or comparative value, such as:

- Before/after screenshots.
- Sample inputs and outputs.
- Migration dry-run output.
- Benchmark data.

Production source paths are recorded by git history. Mention planned source changes in `## Change Plan` when they help scope the work.

## Done rule

A task should not be marked `done` until:

- Acceptance criteria are satisfied.
- Required tests or verification steps have passed, or the issue explains why they are not applicable.
- Relevant knowledge pages are updated when the task changes architecture, domain, NFRs, CI, specs, use cases, or research conclusions.
- Any follow-up feedback is captured as review items rather than hidden in comments.

## Comments and discussion

Use comments for:

- Implementation discussion.
- Work notes.
- Test output summaries.
- Review feedback.
- Blocker resolution.
- Closing rationale when the final result, scope, or reason is not obvious from
  the body.

Keep the task body as the current compact contract.

## Common mistakes

- Missing `## Description`, `## Unit Test Strategy`, or `## Acceptance Criteria`.
- Creating an anchorless task for work that really needs a use case or spec.
- Treating comments as the only source of acceptance criteria.
- Marking `done` without updating affected knowledge pages.
- Embedding long design decisions in the task body instead of creating or updating a spec.
- Using local projection paths or local integer ids as canonical identity.

## Do not

- Do not create local Markdown task files unless explicitly using a local projection workflow.
- Do not use closing keywords or Smart Commit commands unless the workflow intentionally wants automated side effects.
- Do not auto-trigger a skill just because a task is being written; follow the authoring resolver policy.
