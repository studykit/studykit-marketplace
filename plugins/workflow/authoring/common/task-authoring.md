# Workflow Task Authoring

A workflow task records regular implementation work: new functionality,
extension, refactor, or other planned code change.

Companion contracts:

- `./issue-body.md`
- Issue rules: `./issue-authoring.md`

## Task title

Use a short human-readable title that names the intended change and the main
target area.

## Anchors and scope

A task should usually have at least one acceptance source:

- A use case or requirement the task delivers.
- A spec or knowledge page that defines the implementation contract.
- An epic or parent issue that coordinates a batch of work.

Anchorless tasks are allowed for small, obvious changes, but they should pass a smell check:

- If the task implies user-facing behavior with no use case, create or link a use case.
- If the task implies a protocol, schema, API shape, or architectural decision with no spec, create or link a spec.
- If the task is exploratory and evidence is missing, use `spike` or `research` instead.

Do not hide design decisions only in the task body when they should become curated knowledge.

## Shared narrative

When a task belongs to a larger batch of work, keep shared context in the parent
issue. The task body should record only the scope, acceptance criteria, and
implementation notes that are specific to this task.

## Granularity

Split a task when it spans:

- Unrelated code areas.
- Independent acceptance criteria.
- Independent test surfaces.
- Work that can be assigned or sequenced independently.

Record ordering constraints when split tasks must happen in a specific sequence.
Use an epic or parent issue when siblings need shared coordination.

## Body shape

Required:

```markdown
## Description

<what and why>

## Unit Test Strategy

<scenarios, isolation strategy, and expected test locations>

## Acceptance Criteria

- <observable completion condition>
```

`## Acceptance Criteria` must exist even when the task has issue links to use cases or specs.

`## Description` must include why the task exists, not only what will change.
State the motivation explicitly for removals, boundary changes, agent
responsibility changes, schema or contract changes, and work that prevents a
known regression.

Use `## Change Plan` for the expected implementation scope. Do not hide the
motivation only in the plan. If the rationale is a long-lived design decision,
create or update the relevant knowledge page instead of embedding the full
decision record in the task body.

Acceptance criteria should be grounded in:

- Linked use case flow, validation, and error handling.
- Linked spec specification.
- Linked architecture/domain context.
- Explicit user request when no curated page exists yet.

Optional sections:

- `## Change Plan` — forward-looking scope fence naming files, packages, APIs, or migration steps expected to change.
- `## Interface Contracts` — contracts this task consumes or provides.
- `## Resume` — current-state snapshot while mid-flight. See `./issue-body.md`.
- `## Why Discarded` — reason when discarded. See `./issue-body.md`.

Unknown Title Case H2 headings are tolerated.

## Evidence-readiness

A task that is ready for implementation should be actionable as a handoff.

Before treating a task as ready, check that the issue body or linked references provide enough evidence for implementation:

- Reproduction or invocation command when relevant.
- Code coordinates or expected implementation area.
- Data flow or API contract when relevant.
- Current baseline behavior.
- Test fixture or test strategy.

If two or more evidence categories are unknown, consider `spike` or `research` instead of `task`.

## Artifacts

Issue-backed tasks usually do not need a local evidence directory.

Use linked external evidence only when they have evidentiary or comparative value, such as:

- Before/after screenshots.
- Sample inputs and outputs.
- Migration dry-run output.
- Benchmark data.

Production source paths are recorded by git history. Mention planned source changes in `## Change Plan` when they help scope the work.

## Completion criteria

Treat a task as complete only when:

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
- Treating a task as complete without updating affected knowledge pages.
- Embedding long design decisions in the task body instead of creating or updating a spec.
