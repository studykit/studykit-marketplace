# Workflow Spike Authoring

A workflow spike is an **issue-backed, time-boxed exploration to unblock a decision**. It may involve throwaway code, a proof of concept, benchmark, integration probe, or focused technical experiment.

Use `research` for written investigation without throwaway code. Use `task` when the implementation path is known and production work can begin.

Spikes are stored in the configured issue backend. They are not local Markdown files in provider-backed mode.

Companion contracts:

- `./metadata-contract.md`
- `./issue-body.md`
- Issue provider binding: `./providers/issue-authoring.md`
- Provider-specific binding: `./providers/github-issue-authoring.md` or `./providers/jira-issue-authoring.md`

## Storage role

`spike` is stored in the issue backend.

Supported issue providers:

- GitHub Issues
- Jira

Provider identity replaces local integer ids. Use GitHub issue numbers or Jira keys.

## Required metadata

Represent this metadata using provider-native fields when available. If a provider cannot store a field structurally, include the value in the issue body.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `spike`. Use issue type, label, or field depending on provider. |
| `title` | yes | Short description of the question or experiment. |
| `status` | yes | Provider-backed lifecycle status. |
| `depends_on` | optional | Work items that must finish first. Use provider-native metadata when available. Body fallback is provider-specific. |
| `parent` | optional | Task, bug, research item, or epic that spawned or coordinates the spike. Use provider-native metadata when available. Body fallback is provider-specific. |
| `related` | optional | Specs, use cases, research, reviews, pages, or issues relevant to the experiment. |
| `artifact_links` | recommended when PoC exists | Links to branch, gist, repository path, build output, benchmark result, or other throwaway artifact. |
| `labels` | optional | Provider labels/tags. |

Do not use implementation-only fields such as `implements` or implementation cycle counters for spikes.

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

Status meaning:

- `open` — Captured but not yet scoped.
- `queued` — Hypothesis and validation method are clear enough to run.
- `progress` — Experiment is active.
- `holding` — Paused for access, input, or sequencing.
- `failing` — Experiment failed, framing is wrong, or the validation method is blocked.
- `done` — The spike answered the question or clearly invalidated the hypothesis.
- `discarded` — No longer needed.

Provider mappings may vary:

- GitHub: Issue Field status when available.
- Jira: configured Jira workflow statuses.

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
- `## Related` or `## References` — supporting specs, architecture pages, research, tasks, or reviews.
- `## Follow-Up` — task, spec, review, or research item that should exist after the spike.
- `## Resume` — current-state snapshot while mid-flight. See `./issue-body.md`.
- `## Log` — use sparingly; prefer provider comments for discussion and routine logs. See `./issue-body.md`.
- `## Why Discarded` — reason when discarded. See `./issue-body.md`.

Unknown Title Case H2 headings are tolerated.

## Artifact handling

Provider-backed spikes should link to artifacts instead of assuming a local artifact directory.

Acceptable artifact links include:

- A throwaway branch.
- A gist or scratch repository.
- A local projection path when explicitly configured.
- Benchmark output.
- Screenshots or traces.
- Prototype code under a clearly marked scratch location.

PoC code should remain throwaway. If the outcome should become production code, create a follow-up `task` rather than turning the spike into the task.

## Done rule

A spike should not be marked `done` until:

- The hypothesis is answered or invalidated.
- Evidence is linked or summarized.
- The decision impact is clear.
- Follow-up work is captured as a task, spec, research item, or review when needed.
- Any curated knowledge page that should record the outcome has been updated.

`done` does not mean production code shipped. It means the exploration produced an answer.

## Follow-up work

Common follow-ups:

- `task` — implement the chosen approach.
- `spec` — record a contract or decision discovered by the spike.
- `research` — perform deeper written investigation.
- `review` — capture a gap, question, or finding surfaced by the spike.

Link follow-ups visibly in `## Follow-Up` or provider comments.

## Comments and discussion

Use provider comments for:

- Experiment notes.
- Intermediate command output.
- Failed attempts.
- Links discovered midstream.
- Discussion of what the evidence means.

Keep the spike body as the current compact experiment contract.

## Common mistakes

- Using `spike` for production implementation work.
- Missing `## Hypothesis` or `## Validation Method`.
- Marking `done` without evidence.
- Letting throwaway PoC code become production code without a follow-up task.
- Using spike when a written `research` item would be enough.
- Using local projection paths or local integer ids as provider-backed identity.

## Do not

- Do not use `implements` or implementation cycle fields on spikes.
- Do not mark a spike `done` just because time expired; record `failing`, `holding`, or `discarded` if the question was not answered.
- Do not use closing keywords or Smart Commit commands unless the workflow intentionally wants provider side effects.
- Do not auto-trigger a skill just because a spike is being written; follow the authoring resolver policy.
