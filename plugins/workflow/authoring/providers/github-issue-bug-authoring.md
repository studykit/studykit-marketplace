# GitHub Issue Bug Authoring

Provider-specific binding for workflow `bug` artifacts stored as GitHub Issues.

Read after:

- `../common/bug-authoring.md`
- `./github-issue-convention.md`
- `./github-issue-anti-patterns.md`

## Scope

Use this binding for GitHub `bug` issues. The final body structure is listed below.

## Final body structure

Use this final GitHub body structure for `bug` artifacts.

Common required sections are defined by `../common/bug-authoring.md`:

- `## Description`
- `## Reproduction`
- `## Unit Test Strategy`
- `## Acceptance Criteria`

Common optional sections are defined by `../common/bug-authoring.md` and `../common/body-conventions.md`:

- `## Environment`
- `## Change Plan`
- `## Interface Contracts`
- `## Resume`
- `## Why Discarded`

GitHub-specific H2 sections for this type: `## Related`.

GitHub-specific rules:

- Add `## Related` only for soft diagnostic context.
- Do not add dependency body sections.

## Metadata mapping

Recommended GitHub type label: `bug`.

Use GitHub Issue Fields for workflow status when available. If fields are unavailable, use a status label such as `workflow/status:<state>`.

## GitHub-specific section guidance

### `## Related`

Use only for soft diagnostic references that help explain or investigate the defect.

Content:

- Start with one bullet per related artifact.
- Keep descriptions short.
- Do not include blockers, parent issues, or dependency relationships.

## Forbidden body sections

Do not add GitHub-native parent or dependency relationships as body sections. In particular, do not add `## Parent`, `## Dependencies`, `## Blocked`, `## Blocked By`, or `## Blocking`.
