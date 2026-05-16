# Workflow Spike Authoring

A workflow spike is an **issue-backed, time-boxed exploration to unblock a decision**. It may involve throwaway code, a proof of concept, benchmark, integration probe, or focused technical experiment.

Use `research` for written investigation without throwaway code. Use `task` when the implementation path is known and production work can begin.

Companion contracts:

- `./issue-body.md`
- Issue rules: `./issue-authoring.md`

## Spike vs task vs research

Use `spike` when:

- A concrete experiment is needed.
- Throwaway code or a proof of concept may be created.
- A decision is blocked by technical uncertainty.
- The output is evidence that enables a later task or spec.

Use `task` when:

- The implementation approach is known.
- Work should go directly into production code.
- Acceptance criteria are already clear.

Use `research` when:

- The output is written evidence, source review, or comparison.
- No throwaway code or runnable experiment is needed.

## Body shape

Required:

```markdown
## Description

<question being explored, why a spike is needed, and what decision it will inform>

## Hypothesis

<what the spike is trying to prove, disprove, or measure>

## Validation Method

<experiment, benchmark, integration probe, prototype, or sample-driven check>

## Acceptance Criteria

- <observable outcome that answers the question>
```

Optional sections:

- `## Artifact Links` — branch, gist, repository path, benchmark output, screenshots, or other throwaway evidence.
- `## Change Plan` — planned experiment files, temporary branches, scripts, or environments.
- `## Resume` — current-state snapshot while mid-flight. See `./issue-body.md`.
- `## Why Discarded` — reason when discarded. See `./issue-body.md`.

Unknown Title Case H2 headings are tolerated.

## Artifact handling

Issue-backed spikes should link to evidence or output files instead of assuming a local evidence directory.

Acceptable links include:

- A throwaway branch.
- A gist or scratch repository.
- A local projection path when explicitly configured.
- Benchmark output.
- Screenshots or traces.
- Prototype code under a clearly marked scratch location.

PoC code should remain throwaway. If the outcome should become production code, create a follow-up `task` rather than turning the spike into the task.

## Done rule

A spike is complete when:

- The hypothesis is answered or invalidated.
- Evidence is linked or summarized.
- The decision impact is clear.
- Follow-up work is captured as a task, spec, research item, or review when needed.
- Any curated knowledge page that should record the outcome has been updated.

Completion does not mean production code shipped. It means the exploration produced an answer.

## Follow-up work

Common follow-ups:

- `task` — implement the chosen approach.
- `spec` — record a contract or decision discovered by the spike.
- `research` — perform deeper written investigation.
- `review` — capture a gap, question, or finding surfaced by the spike.

Link follow-ups visibly in the issue body or comments.

## Comments and discussion

Use comments for:

- Experiment notes.
- Intermediate command output.
- Failed attempts.
- Links discovered midstream.
- Discussion of what the evidence means.

Keep the spike body as the current compact experiment contract.

## Common mistakes

- Using `spike` for production implementation work.
- Missing `## Hypothesis` or `## Validation Method`.
- Treating the spike as complete without evidence.
- Letting throwaway PoC code become production code without a follow-up task.
- Using spike when a written `research` item would be enough.

## Do not

- Do not treat a spike as complete just because time expired; record what remains unanswered.
