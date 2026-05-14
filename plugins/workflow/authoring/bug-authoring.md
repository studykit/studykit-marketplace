# Workflow Bug Authoring

A workflow bug is an **issue-backed defect fix** against expected behavior. It tracks production behavior that is wrong, missing, regressed, or inconsistent with a use case, spec, test expectation, or user-visible contract.

Bugs are stored in the configured issue backend. They are not local Markdown files in provider-backed mode.

Companion contracts:

- `./metadata-contract.md`
- `./issue-body.md`
- Provider binding: `./providers/github-issue-authoring.md` or `./providers/jira-issue-authoring.md`

## Storage role

`bug` is stored in the issue backend.

Supported issue providers:

- GitHub Issues
- Jira

Provider identity replaces local integer ids. Use GitHub issue numbers or Jira keys.

## Required metadata

Represent this metadata using provider-native fields when available. If a provider cannot store a field structurally, include the value in the issue body.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | Always `bug`. Use issue type, label, or field depending on provider. |
| `title` | yes | Short summary of the broken behavior. |
| `status` | yes | Provider-backed lifecycle status. |
| `severity` | recommended | Provider priority/severity if available. |
| `implements` | optional | Use case affected by the bug. Metadata when possible, `## Implements` or `## Related` in body when present. |
| `spec` | optional | Spec or knowledge artifact whose expected behavior is violated. |
| `depends_on` | optional | Blocking or ordering dependency. Use provider-native metadata when available. Do not add blocked/dependency body sections for GitHub Issues. |
| `parent` | optional | Epic or parent issue coordinating the fix. |
| `related` | optional | Non-blocking references useful for diagnosis or implementation. |
| `labels` | optional | Provider labels/tags. |

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

Provider mappings may vary:

- GitHub: use Issue Field status when available; labels or project fields are fallback/planning views.
- Jira: map to configured Jira workflow statuses.

Status meaning:

- `open` — Captured but not yet ready for fix.
- `queued` — Reproduction and expected behavior are clear enough to fix.
- `progress` — Fix is active.
- `holding` — Paused for input, access, or sequencing.
- `failing` — Fix attempt failed or reproduction is unstable.
- `done` — Regression is fixed and verified.
- `discarded` — No longer applicable or intentionally not fixing.

`open` is the default initial status unless the user explicitly asks to queue it.

## Evidence-readiness

A bug without a reproducible failure path is not ready for implementation.

Before moving to `queued`, capture enough evidence for a handoff:

- Reproduction steps or command.
- Observed behavior.
- Expected behavior.
- Environment, version, data shape, or relevant conditions.
- Code coordinates or suspected component when known.
- Test fixture or regression test strategy.

If reproduction is unknown and the task is mostly discovery, use `spike` or `research` instead of `bug` until the defect is pinned down.

## Body shape

Required:

```markdown
## Description

<what is broken, observed behavior, expected behavior, and why it matters>

## Reproduction

<steps, command, data, or conditions that reproduce the bug>

## Unit Test Strategy

<regression test scenario, isolation strategy, and expected test locations>

## Acceptance Criteria

- <bug no longer reproduces>
- <regression test fails before fix and passes after fix>
```

`## Acceptance Criteria` must exist even when the bug is linked to a use case or spec.

Optional sections:

- `## Environment` — version, browser, OS, tenant, data shape, feature flags, or deployment context.
- `## Implements` — when the bug traces to a use case requirement.
- `## Dependencies` — use only when the active provider binding requires a body fallback. Do not include blocked/dependency sections for GitHub Issues.
- `## Related` or `## References` — supporting knowledge pages, logs, prior issues, specs, or research.
- `## Change Plan` — forward-looking scope fence naming files, packages, APIs, or migration steps expected to change.
- `## Interface Contracts` — contracts the fix consumes or restores.
- `## Resume` — current-state snapshot while mid-flight. See `./issue-body.md`.
- `## Log` — use sparingly; prefer provider comments for discussion and routine logs. See `./issue-body.md`.
- `## Why Discarded` — reason when discarded. See `./issue-body.md`.

Unknown Title Case H2 headings are tolerated.

## Regression test rule

A bug should end with a regression test when technically feasible.

The test should:

- Fail before the fix or describe why pre-fix failure cannot be demonstrated safely.
- Pass after the fix.
- Pin the expected behavior that was violated.

If no automated regression test is feasible, document the manual verification path and reason in `## Unit Test Strategy`.

## Anchors and scope

A bug may link to:

- A use case whose flow or expected outcome is violated.
- A spec whose contract is violated.
- An architecture/domain/NFR/CI page affected by the fix.
- A parent epic or task where the bug was discovered.

If the bug reveals that expected behavior is undocumented, create a review item with `kind: gap` targeting the missing knowledge artifact.

## Artifacts

Provider-backed bugs usually do not need a local artifact directory.

Use linked external artifacts only when evidence has lasting value, such as:

- Screenshots.
- Crash logs.
- Traces.
- Minimal repro repositories.
- Problematic input files.

Production source paths are recorded by git history. Mention planned source changes in `## Change Plan` when they help scope the fix.

## Done rule

A bug should not be marked `done` until:

- Reproduction no longer fails, or the issue explains why the original reproduction is obsolete.
- Regression test or manual verification is complete.
- Acceptance criteria are satisfied.
- Affected knowledge pages are updated when the bug changes documented behavior, architecture, domain, NFRs, CI, specs, use cases, or research conclusions.
- Follow-up feedback is captured as review items rather than hidden in comments.

## Comments and discussion

Use provider comments for:

- Diagnosis discussion.
- Logs and screenshots discovered after creation.
- Fix attempt notes.
- Review feedback.
- Verification summaries.

Keep the bug body as the current compact defect contract.

## Common mistakes

- Missing `## Reproduction`.
- Missing `## Unit Test Strategy` or regression test plan.
- Capturing a vague symptom as `queued` before reproduction is clear.
- Treating provider comments as the only source of expected behavior.
- Marking `done` without a regression test or documented manual verification.
- Using local projection paths or local integer ids as provider-backed identity.

## Do not

- Do not create local Markdown bug files in provider-backed mode unless explicitly using a local projection workflow.
- Do not ship a fix without a regression test or a clear reason why one is not feasible.
- Do not use closing keywords or Smart Commit commands unless the workflow intentionally wants provider side effects.
- Do not auto-trigger a skill just because a bug is being written; follow the authoring resolver policy.
