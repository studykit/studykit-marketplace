# GitHub Issue Task Authoring

Provider-specific binding for workflow `task` artifacts stored as GitHub Issues.

Read after:

- `../common/task-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-metadata.md`
- `./github-issue-relationships.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `task` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `task` artifacts.

Common required sections are defined by `../common/task-authoring.md`:

- `## Description`
- `## Unit Test Strategy`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/task-authoring.md` and `../common/body-conventions.md`:

- `## Change Plan`
- `## Interface Contracts`
- `## Resume`
- `## Why Discarded`

GitHub-specific H2 sections for this type: `## Implements`, `## Related`.

GitHub-specific rules:

- Add `## Implements` when the task implements a use case, requirement, spec, or knowledge page.
- Add `## Related` only for soft, non-blocking references.
- Do not add `## Parent`, `## Dependencies`, or blocked/dependency sections.

## Metadata mapping

Recommended GitHub type label: `task`.

Use GitHub Issue Fields for workflow status when available. If fields are unavailable, use a status label such as `workflow/status:<state>`.

## GitHub-specific section guidance

### `## Implements`

Use when the task implements a use case, requirement, spec, or curated page.

Content:

- Start with one bullet per implemented artifact.
- Use `#123` for same-repository workflow issues.
- Use `owner/repo#123` for cross-repository GitHub issues.
- Use Markdown links for repository knowledge pages or external pages.
- Do not use this section for parent, dependency, or sequencing relationships.

### `## Related`

Use only for soft, non-blocking references that are useful implementation context.

Content:

- Start with one bullet per related artifact.
- Keep descriptions short.
- Do not include blockers, parent issues, implementation targets, or sequencing constraints.

## Forbidden body sections

Do not add GitHub-native parent or dependency relationships as body sections. In particular, do not add `## Parent`, `## Dependencies`, `## Blocked`, `## Blocked By`, or `## Blocking`.
